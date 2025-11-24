# gui_power_extended.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Try to import project modules (these should exist in the repo). If they fail, fall back
# to local implementations.
try:
    from zth_to_foster import fit_foster_from_zth  # expected: (t_pts, zth_pts, order_N) -> (R_f, C_f)
except Exception:
    fit_foster_from_zth = None
try:
    from foster_to_cauer import foster_to_cauer  # expected: (R_f, C_f) -> (R_c, C_c)
except Exception:
    foster_to_cauer = None

from typing import Tuple

# --- Local fallbacks ---

def _local_time_curve_from_foster(t: np.ndarray, R: np.ndarray, C: np.ndarray) -> np.ndarray:
    # step response of Foster ladder: z(t) = sum_i R_i*(1-exp(-t/(R_i*C_i)))
    t = np.asarray(t, float)
    R = np.asarray(R, float)
    C = np.asarray(C, float)
    tau = R*C
    return np.sum(R * (1.0 - np.exp(-np.outer(t, 1.0/np.maximum(tau, 1e-300)))), axis=1)

def _local_foster_to_cauer(R_f, C_f):
    # fallback: return the input as "Cauer" (placeholder) — the repo's foster_to_cauer should be used.
    # We keep shape but mark that it's passthrough.
    return np.array(R_f), np.array(C_f)

# Duty estimation (robust and simple)
def estimate_duty_cycle(t: np.ndarray, P: np.ndarray) -> Tuple[float, float, float]:
    if t.size < 5:
        peak = np.max(P) if P.size>0 else 0.0
        avg = np.mean(P) if P.size>0 else 0.0
        duty = (avg/peak) if peak>0 else 0.0
        return duty, 0.0, 0.0
    duration = float(t[-1] - t[0])
    n_uniform = min(2000, max(200, int(duration / np.median(np.diff(t)))))
    t_uniform = np.linspace(t[0], t[-1], n_uniform)
    P_uniform = np.interp(t_uniform, t, P)
    P0 = P_uniform - np.mean(P_uniform)
    window = np.hanning(len(P0))
    Pw = P0 * window
    fft = np.fft.rfft(Pw)
    freqs = np.fft.rfftfreq(len(Pw), d=(t_uniform[1]-t_uniform[0]))
    mag = np.abs(fft)
    mag[0] = 0.0
    if np.all(mag==0):
        thr = 0.5*(np.nanmin(P)+np.nanmax(P))
        on = P>thr
        duty = np.mean(on)
        return duty, 0.0, thr
    idx = np.argmax(mag)
    f_dom = freqs[idx]
    period = 1.0/f_dom if f_dom>0 else duration
    thr = 0.5*(np.nanmin(P) + np.nanmax(P))
    on_mask = P_uniform > thr
    if np.any(on_mask):
        edges = np.diff(on_mask.astype(int))
        starts = np.where(edges==1)[0]+1
        stops  = np.where(edges==-1)[0]+1
        if on_mask[0]: starts = np.concatenate(([0], starts))
        if on_mask[-1]: stops = np.concatenate((stops, [len(on_mask)]))
        widths = (stops - starts) * (t_uniform[1]-t_uniform[0])
        avg_width = float(np.mean(widths)) if widths.size>0 else 0.0
    else:
        avg_width = 0.0
    duty = float(avg_width / period) if period>0 else 0.0
    duty = max(0.0, min(1.0, duty))
    return duty, period, thr

# Build Zth (step) from Cauer R,C: we expect the provided cauer RC to represent a ladder; convert to step
# (For safety we'll accept either foster or cauer arrays and use numerical step-response via RC network)
def zth_step_from_cauer(t: np.ndarray, R_c: np.ndarray, C_c: np.ndarray) -> np.ndarray:
    # Simple numerical step response of series Cauer ladder: approximate by summing first-order terms
    tau = np.asarray(R_c, float) * np.asarray(C_c, float)
    return np.sum(np.asarray(R_c) * (1.0 - np.exp(-np.outer(t, 1.0/np.maximum(tau,1e-300)))), axis=1)

# Convolution to get temperature
def temp_from_power_and_zth(t_grid: np.ndarray, P_t: np.ndarray, Zth_t: np.ndarray) -> np.ndarray:
    # discrete conv: T(t) = integral_0^t P(s) * h(t-s) ds, where h = dZth/dt
    h = np.gradient(Zth_t, t_grid)
    P_interp = np.interp(t_grid, t_grid, P_t)
    dt = np.gradient(t_grid)
    conv = np.convolve(P_interp, h)[:len(t_grid)] * dt.mean()
    return conv

# simple CSV loader
def load_two_col_csv(path: str):
    data = np.genfromtxt(path, delimiter=',', dtype=float)
    if data.ndim == 1 or data.shape[1] < 2:
        raise ValueError('CSV must have at least two columns')
    x = data[:,0].astype(float); y = data[:,1].astype(float)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]; y = y[mask]
    order = np.argsort(x)
    return x[order], y[order]

# --- GUI ---
class ExtendedPowerTempApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Power→Temp (uses project Zth→Foster & Foster→Cauer when available)')
        self.geometry('1250x820')
        self._build()
        self._clear_state()

    def _clear_state(self):
        self.t_p = None; self.P = None
        self.zth_t = None; self.zth_val = None
        self.Rf = None; self.Cf = None
        self.Rc = None; self.Cc = None
        self._last = None

    def _build(self):
        left = ttk.Frame(self, padding=8); left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text='Inputs', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        ttk.Button(left, text='1) Load power CSV [t(s), P(W)]', command=self._on_load_power).pack(fill=tk.X, pady=4)
        ttk.Button(left, text='2) Load Zth vs tp CSV [tp(s), Zth(K/W)]', command=self._on_load_zth).pack(fill=tk.X, pady=4)

        ttk.Label(left, text='Order N (Foster/Cauer)').pack(anchor='w', pady=(8,0))
        self.var_order = tk.StringVar(value='4')
        ttk.Entry(left, textvariable=self.var_order, width=8).pack(anchor='w')

        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=8)
        ttk.Label(left, text='Optional heatsink extension (enter any to enable)').pack(anchor='w')
        ttk.Label(left, text='Heatsink R_th (K/W)').pack(anchor='w')
        self.var_h_Rth = tk.StringVar(value='')
        ttk.Entry(left, textvariable=self.var_h_Rth, width=12).pack(anchor='w')
        ttk.Label(left, text='Heatsink C_th (J/K)').pack(anchor='w')
        self.var_h_Cth = tk.StringVar(value='')
        ttk.Entry(left, textvariable=self.var_h_Cth, width=12).pack(anchor='w')

        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=8)
        ttk.Label(left, text='Simulation settings', font=('TkDefaultFont', 10, 'bold')).pack(anchor='w')
        ttk.Label(left, text='Ambient temperature (°C)').pack(anchor='w')
        self.var_ambient = tk.StringVar(value='25.0')
        ttk.Entry(left, textvariable=self.var_ambient, width=10).pack(anchor='w')
        ttk.Label(left, text='Total simulation time (s) — leave blank to auto (3 periods)').pack(anchor='w')
        self.var_total_time = tk.StringVar(value='')
        ttk.Entry(left, textvariable=self.var_total_time, width=12).pack(anchor='w')

        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=8)
        ttk.Button(left, text='Compute →', command=self._on_compute).pack(fill=tk.X, pady=6)
        ttk.Button(left, text='Export results CSV/NPZ', command=self._on_export).pack(fill=tk.X)

        # Right side: tabs and results
        right = ttk.Frame(self, padding=8); right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.nb = ttk.Notebook(right); self.nb.pack(fill=tk.BOTH, expand=True)

        self.fig_power = Figure(figsize=(6,3), dpi=100); self.ax_power = self.fig_power.add_subplot(111)
        self.canvas_power = FigureCanvasTkAgg(self.fig_power, master=self.nb); self.nb.add(self.canvas_power.get_tk_widget(), text='Power')

        self.fig_zth = Figure(figsize=(6,3), dpi=100); self.ax_zth = self.fig_zth.add_subplot(111)
        self.canvas_zth = FigureCanvasTkAgg(self.fig_zth, master=self.nb); self.nb.add(self.canvas_zth.get_tk_widget(), text='Zth / Fits')

        self.fig_temp = Figure(figsize=(6,3), dpi=100); self.ax_temp = self.fig_temp.add_subplot(111)
        self.canvas_temp = FigureCanvasTkAgg(self.fig_temp, master=self.nb); self.nb.add(self.canvas_temp.get_tk_widget(), text='Temperature')

        self.txt = tk.Text(right, height=8); self.txt.pack(fill=tk.X, pady=(6,0))

        for ax in (self.ax_power, self.ax_zth, self.ax_temp):
            ax.grid(True); ax.set_xlabel('t (s)')

    def _log(self, msg: str):
        self.txt.insert('end', msg + '')
        self.txt.see('end')

    def _on_load_power(self):
        path = filedialog.askopenfilename(filetypes=[('CSV','*.csv'),('All','*.*')])
        if not path: return
        try:
            t, P = load_two_col_csv(path)
            self.t_p, self.P = t, P
            self.ax_power.clear(); self.ax_power.plot(t,P,'o-'); self.ax_power.set_ylabel('P (W)'); self.canvas_power.draw()
            self._log(f'Loaded power CSV: {path} ({len(t)} points)')
        except Exception as e:
            messagebox.showerror('Load error', str(e))

    def _on_load_zth(self):
        path = filedialog.askopenfilename(filetypes=[('CSV','*.csv'),('All','*.*')])
        if not path: return
        try:
            t, z = load_two_col_csv(path)
            self.zth_t, self.zth_val = t, z
            self.ax_zth.clear(); self.ax_zth.plot(t,z,'o',label='Zth data'); self.ax_zth.set_ylabel('Zth (K/W)'); self.ax_zth.legend(); self.canvas_zth.draw()
            self._log(f'Loaded Zth CSV: {path} ({len(t)} points)')
        except Exception as e:
            messagebox.showerror('Load error', str(e))

    def _on_compute(self):
        self.txt.delete('1.0','end')
        if self.t_p is None or self.P is None:
            messagebox.showerror('Missing data','Load power CSV first'); return
        if self.zth_t is None or self.zth_val is None:
            messagebox.showerror('Missing data','Load Zth vs tp CSV first'); return
        try:
            N = int(self.var_order.get())
        except Exception:
            messagebox.showerror('Order error','Enter integer order N'); return

        # 1) duty
        duty, period, thr = estimate_duty_cycle(self.t_p, self.P)
        duty_pct = duty * 100.0
        self._log(f'Duty (estimated): {duty:.6f} ({duty_pct:.2f} %), Period: {period:.6g} s, Threshold: {thr:.6g} W')

        # 2) Foster fit
        if fit_foster_from_zth is not None:
            try:
                Rf, Cf = fit_foster_from_zth(self.zth_t, self.zth_val, N)
                self._log(f'Foster fit returned {len(Rf)} stages')
            except Exception as e:
                self._log('fit_foster_from_zth failed: ' + str(e))
                Rf, Cf = np.zeros(N), np.ones(N)
        else:
            # fallback: naive log-spaced RC approximation
            self._log('fit_foster_from_zth not available — using naive RC spacing fallback')
            R_total = max(1e-12, np.max(self.zth_val))
            Rf = np.full(N, R_total / N)
            taus = np.logspace(np.log10(self.zth_t[0]+1e-9), np.log10(self.zth_t[-1]+1e-9), N)
            Cf = taus / Rf

        self.Rf, self.Cf = np.asarray(Rf), np.asarray(Cf)

        # 3) Foster -> Cauer
        if foster_to_cauer is not None:
            try:
                Rc, Cc = foster_to_cauer(self.Rf, self.Cf)
                self._log(f'foster_to_cauer returned {len(Rc)} stages')
            except Exception as e:
                self._log('foster_to_cauer failed: ' + str(e)); Rc, Cc = _local_foster_to_cauer(self.Rf, self.Cf)
        else:
            self._log('foster_to_cauer not available — using passthrough fallback (Foster treated as Cauer)')
            Rc, Cc = _local_foster_to_cauer(self.Rf, self.Cf)

        # Optional heatsink extension
        try:
            hR = float(self.var_h_Rth.get()) if self.var_h_Rth.get().strip() != '' else None
            hC = float(self.var_h_Cth.get()) if self.var_h_Cth.get().strip() != '' else None
        except Exception:
            hR = hC = None
        if (hR is not None) and (hC is not None):
            Rc = np.concatenate((Rc, [hR])); Cc = np.concatenate((Cc, [hC]))
            self._log(f'Appended heatsink R={hR:.6g} K/W, C={hC:.6g} J/K as extra Cauer stage')

        self.Rc, self.Cc = np.asarray(Rc), np.asarray(Cc)

        # Ambient and total time
        try:
            ambient = float(self.var_ambient.get())
        except Exception:
            ambient = 25.0
        tt_user = self.var_total_time.get().strip()
        # If user specified a total time use it; otherwise use 3 cycles or data span
        if tt_user != '':
            try:
                total_time = float(tt_user)
                if total_time <= 0:
                    raise ValueError('non-positive')
            except Exception:
                messagebox.showerror('Total time error','Enter positive number for total time'); return
        else:
            total_time = (period if period>0 else (self.t_p[-1]-self.t_p[0])) * 3.0
            if total_time <= 0:
                total_time = self.t_p[-1] - self.t_p[0]
                if total_time <= 0:
                    total_time = 1.0

        # Prepare time grid
        n_points = 3000
        tgrid = np.linspace(0.0, total_time, n_points)

        # Build repeated power waveform by tiling P profile across cycles using modulo mapping
        t_start, t_end = float(self.t_p[0]), float(self.t_p[-1])
        span = t_end - t_start if (t_end - t_start) > 0 else total_time
        def P_single(tt):
            if span <= 0:
                return np.interp(tt, self.t_p, self.P, left=0.0, right=0.0)
            tt_mod = ((tt - t_start) % span) + t_start
            return np.interp(tt_mod, self.t_p, self.P, left=0.0, right=0.0)

        P_on_grid = P_single(tgrid)

        # Compute Zth step response from Cauer
        Zth_grid = zth_step_from_cauer(tgrid, self.Rc, self.Cc)

        # Temperature (delta T)
        T_delta = temp_from_power_and_zth(tgrid, P_on_grid, Zth_grid)
        T_abs = T_delta + ambient

        # Plot results
        self.ax_power.clear(); self.ax_power.plot(tgrid, P_on_grid, '-', label='P (repeated)'); self.ax_power.plot(self.t_p, self.P, 'o', label='original'); self.ax_power.set_ylabel('P (W)'); self.ax_power.legend(); self.canvas_power.draw()

        # Plot zth and fits
        self.ax_zth.clear(); self.ax_zth.plot(self.zth_t, self.zth_val, 'o', label='Zth data')
        try:
            zf = _local_time_curve_from_foster(self.zth_t, self.Rf, self.Cf)
            self.ax_zth.plot(self.zth_t, zf, '-', label='Foster fit')
        except Exception:
            pass
        zr = zth_step_from_cauer(self.zth_t, self.Rc, self.Cc)
        self.ax_zth.plot(self.zth_t, zr, '--', label='Cauer step (recon)')
        self.ax_zth.set_ylabel('Zth (K/W)'); self.ax_zth.legend(); self.canvas_zth.draw()

        self.ax_temp.clear(); self.ax_temp.plot(tgrid, T_abs, '-', label='T (°C)'); self.ax_temp.plot(tgrid, T_delta, '--', label='ΔT (K)'); self.ax_temp.set_ylabel('Temperature (°C)'); self.ax_temp.legend(); self.canvas_temp.draw()

        # Fill textual outputs
        self._log('--- Results ---')
        self._log(f'Ambient temperature = {ambient:.3f} °C')
        self._log(f'Total simulation time = {total_time:.6g} s')
        self._log(f'Duty = {duty:.6f} ({duty_pct:.2f} %)')
        self._log(f'Foster R (N={len(self.Rf)}): ' + ', '.join([f'{x:.6g}' for x in self.Rf]))
        self._log(f'Foster C (N={len(self.Cf)}): ' + ', '.join([f'{x:.6g}' for x in self.Cf]))
        self._log(f'Cauer R (N={len(self.Rc)}): ' + ', '.join([f'{x:.6g}' for x in self.Rc]))
        self._log(f'Cauer C (N={len(self.Cc)}): ' + ', '.join([f'{x:.6g}' for x in self.Cc]))

        self._last = dict(tgrid=tgrid, P=P_on_grid, Zth=Zth_grid, T_delta=T_delta, T_abs=T_abs, duty=duty, duty_pct=duty_pct, Rf=self.Rf, Cf=self.Cf, Rc=self.Rc, Cc=self.Cc, ambient=ambient, total_time=total_time)

    def _on_export(self):
        if not self._last:
            messagebox.showinfo('Nothing','Compute first'); return
        path = filedialog.asksaveasfilename(defaultextension='.npz', filetypes=[('NPZ','*.npz'),('CSV','*.csv')])
        if not path: return
        if path.endswith('.npz'):
            np.savez(path, **self._last)
            messagebox.showinfo('Exported', f'Saved NPZ: {path}')
        else:
            # CSV export t, P, Zth, T_delta, T_abs
            import csv
            with open(path,'w',newline='') as f:
                w = csv.writer(f)
                w.writerow(['t_s','P_W','Zth_K_per_W','dT_K','T_C'])
                for ti,Pi,zi,Ti_delta,Ti_abs in zip(self._last['tgrid'], self._last['P'], self._last['Zth'], self._last['T_delta'], self._last['T_abs']):
                    w.writerow([f'{ti:.9g}', f'{Pi:.9g}', f'{zi:.9g}', f'{Ti_delta:.9g}', f'{Ti_abs:.9g}'])
            # Also write a small metadata file
            meta_path = path + '.meta.txt'
            with open(meta_path,'w') as m:
                m.write(f"Duty_pct: {self._last['duty_pct']:.6f}")
                m.write(f"Ambient_C: {self._last['ambient']:.6f}")
                m.write(f"Total_time_s: {self._last['total_time']:.6g}")
                m.write('Foster_R: ' + ','.join([str(x) for x in self._last['Rf']]) + '')
                m.write('Foster_C: ' + ','.join([str(x) for x in self._last['Cf']]) + '')
                m.write('Cauer_R: ' + ','.join([str(x) for x in self._last['Rc']]) + '')
                m.write('Cauer_C: ' + ','.join([str(x) for x in self._last['Cc']]) + '')
            messagebox.showinfo('Exported', f'CSV saved: {path}Metadata: {meta_path}')

if __name__ == '__main__':
    ExtendedPowerTempApp().mainloop()