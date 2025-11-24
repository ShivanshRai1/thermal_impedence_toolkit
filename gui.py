import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from utils_io import load_zth_csv
from zth_to_foster import fit_foster, zth_from_foster as zth_from_foster_fit
from foster_to_cauer import foster_to_cauer
from thermal_predictor import scale_foster_by_area, zth_from_foster as zth_from_foster_predict

def foster_time_curve(t, R, C):
    tau = np.asarray(R)*np.asarray(C)
    t = np.asarray(t, float)
    return (1.0 - np.exp(-np.outer(t, 1.0/np.maximum(tau, 1e-300)))) @ np.asarray(R)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Thermal Impedance Toolkit")
        self.geometry("1200x780")
        self.minsize(1000, 680)
        self.t = self.z = None
        self.Rf = self.Cf = None
        self.Rc = self.Cc = None
        self.Rf_new = self.Cf_new = None
        self._build()

    def _build(self):
        left = ttk.Frame(self, padding=10); left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="1) Load Zth vs t (CSV)").pack(anchor='w')
        ttk.Button(left, text="Choose CSV...", command=self._on_load).pack(anchor='w', pady=(0,8))

        frm = ttk.LabelFrame(left, text="Inputs", padding=8); frm.pack(fill=tk.X, pady=6)
        ttk.Label(frm, text="Order N").grid(row=0, column=0, sticky='w')
        self.var_N = tk.StringVar(value='4')
        ttk.Entry(frm, textvariable=self.var_N, width=8).grid(row=0, column=1, sticky='w', padx=6)

        ttk.Label(frm, text="Ref Die Area").grid(row=1, column=0, sticky='w')
        self.var_Aref = tk.StringVar(value='1.0')
        ttk.Entry(frm, textvariable=self.var_Aref, width=10).grid(row=1, column=1, sticky='w', padx=6)

        ttk.Label(frm, text="New Die Area").grid(row=2, column=0, sticky='w')
        self.var_Anew = tk.StringVar(value='')
        ttk.Entry(frm, textvariable=self.var_Anew, width=10).grid(row=2, column=1, sticky='w', padx=6)

        ttk.Label(frm, text="Gamma mode").grid(row=3, column=0, sticky='w')
        self.gamma_mode = tk.StringVar(value='blended')
        ttk.Combobox(frm, textvariable=self.gamma_mode, values=['blended','fixed'], width=10, state='readonly').grid(row=3, column=1, sticky='w', padx=6)
        ttk.Label(frm, text="Gamma (if fixed)").grid(row=4, column=0, sticky='w')
        self.var_gamma = tk.StringVar(value='0.8')
        ttk.Entry(frm, textvariable=self.var_gamma, width=10).grid(row=4, column=1, sticky='w', padx=6)

        ttk.Button(left, text="Fit Foster", command=self._on_fit_foster).pack(fill=tk.X, pady=6)
        ttk.Button(left, text="Convert to Cauer", command=self._on_to_cauer).pack(fill=tk.X, pady=6)
        ttk.Button(left, text="Predict Sibling", command=self._on_predict).pack(fill=tk.X, pady=6)

        right = ttk.Frame(self, padding=10); right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.nb = ttk.Notebook(right); self.nb.pack(fill=tk.BOTH, expand=True)

        # --- Foster tab ---
        self.fig_fit = Figure(figsize=(6,4), dpi=100); self.ax_fit = self.fig_fit.add_subplot(111)
        self.canvas_fit = FigureCanvasTkAgg(self.fig_fit, master=self.nb); self.nb.add(self.canvas_fit.get_tk_widget(), text="Fit → Foster")
        self.txt_fit = tk.Text(right, height=5); self.txt_fit.pack(fill=tk.X, pady=(6,0))

        # --- Cauer tab ---
        self.fig_cauer = Figure(figsize=(6,4), dpi=100); self.ax_cauer = self.fig_cauer.add_subplot(111)
        self.canvas_cauer = FigureCanvasTkAgg(self.fig_cauer, master=self.nb); self.nb.add(self.canvas_cauer.get_tk_widget(), text="Foster → Cauer")
        self.txt_cauer = tk.Text(right, height=4); self.txt_cauer.pack(fill=tk.X, pady=(6,0))

        # --- Predict tab ---
        self.fig_pred = Figure(figsize=(6,4), dpi=100); self.ax_pred = self.fig_pred.add_subplot(111)
        self.canvas_pred = FigureCanvasTkAgg(self.fig_pred, master=self.nb); self.nb.add(self.canvas_pred.get_tk_widget(), text="Predict Sibling")
        self.txt_pred = tk.Text(right, height=4); self.txt_pred.pack(fill=tk.X, pady=(6,0))

        self._style_plots()

    def _style_plots(self):
        for ax in (self.ax_fit, self.ax_cauer, self.ax_pred):
            ax.set_xscale('log'); ax.grid(True, which='both', alpha=0.3)
            ax.set_xlabel('t (s)'); ax.set_ylabel('Zth (K/W)')

    def _on_load(self):
        path = filedialog.askopenfilename(filetypes=[("CSV","*.csv"),("All","*.*")])
        if not path: return
        try:
            self.t, self.z = load_zth_csv(path)
            messagebox.showinfo("Loaded", f"Loaded {len(self.t)} points. Click 'Fit Foster'.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_fit_foster(self):
        self.txt_fit.delete('1.0','end')
        if self.t is None: messagebox.showerror("No data","Load CSV first."); return
        try:
            N = int(self.var_N.get())
            Rf, Cf, tau, zfit = fit_foster(self.t, self.z, N=N, refine_iters=2)
            self.Rf, self.Cf = Rf, Cf

            ax = self.ax_fit; ax.clear(); self._style_plots()
            ax.plot(self.t, self.z, 'o', ms=4, label='CSV points', zorder=3)
            ax.plot(self.t, zfit, '-', lw=2.4, label='Mathematical fit (Foster)', zorder=2)
            ax.legend(loc='best'); self.canvas_fit.draw()

            dc_last = float(self.z[-1]); dc_sumR = float(np.sum(Rf))
            dc_err_pct = abs(dc_sumR - dc_last) / max(dc_last,1e-12) * 100.0
            rms_rel = float(np.sqrt(np.mean(((zfit - self.z)/np.maximum(self.z, 1e-12))**2)))
            self.txt_fit.insert('end', f'RMS relative error: {rms_rel:.6g}  ({rms_rel*100:.3f} %)\\n')
            self.txt_fit.insert('end', f'DC check: sum(R)={dc_sumR:.6g} vs Zth(last)={dc_last:.6g}  (error {dc_err_pct:.3f} %)\\n')
        except Exception as e:
            messagebox.showerror("Fit error", str(e))

    def _on_to_cauer(self):
        self.txt_cauer.delete('1.0','end')
        if self.Rf is None: messagebox.showerror("No Foster","Fit Foster first."); return
        try:
            Rc, Cc = foster_to_cauer(self.Rf, self.Cf); self.Rc, self.Cc = Rc, Cc
            # t-grid for smooth lines
            tgrid = np.geomspace(max(self.t.min(),1e-9), self.t.max(), 600) if self.t is not None else np.geomspace(1e-9, 1.0, 600)
            z_foster = foster_time_curve(tgrid, self.Rf, self.Cf)
            z_cauer  = foster_time_curve(tgrid, Rc, Rc*Cc)  # approximate time curve for visual equivalence

            ax = self.ax_cauer; ax.clear(); self._style_plots()
            if self.t is not None and self.z is not None:
                ax.plot(self.t, self.z, 'o', ms=3.5, label='CSV points', zorder=4)
            ax.plot(tgrid, z_foster, '-', lw=2.2, label='Input (Foster)', zorder=3)
            ax.plot(tgrid, z_cauer,  '-', lw=2.0, label='Mathematical fit (Cauer equiv)', zorder=2)
            ax.legend(loc='best'); self.canvas_cauer.draw()

            dc_foster = float(np.sum(self.Rf)); dc_cauer = float(np.sum(Rc))
            dc_eq_err = abs(dc_foster - dc_cauer) / max(dc_foster,1e-12) * 100.0
            self.txt_cauer.insert('end', f'DC equality: Foster ∑R={dc_foster:.6g} vs Cauer ∑R={dc_cauer:.6g}  (error {dc_eq_err:.3f} %)\\n')
        except Exception as e:
            messagebox.showerror("Cauer error", str(e))

    def _on_predict(self):
        self.txt_pred.delete('1.0','end')
        if self.Rf is None: messagebox.showerror("No Foster","Fit Foster first."); return
        try:
            Aref = float(self.var_Aref.get())
            Anew_txt = self.var_Anew.get().strip()
            if not Anew_txt: messagebox.showinfo("Missing area","Enter New Die Area."); return
            Anew = float(Anew_txt)
            gam = float(self.var_gamma.get()) if self.gamma_mode.get()=='fixed' else 'blended'

            # Dense grid for fits
            tgrid = np.geomspace(max(self.t.min(),1e-9), self.t.max(), 600)
            zfit_ref = foster_time_curve(tgrid, self.Rf, self.Cf)

            Rn, Cn, g = scale_foster_by_area(self.Rf, self.Cf, Aref, Anew, gamma=gam)
            self.Rf_new, self.Cf_new = Rn, Cn
            zfit_new = zth_from_foster_predict(tgrid, Rn, Cn)

            # Predicted points at the CSV time stamps (for visibility)
            z_pts_pred = zth_from_foster_predict(self.t, Rn, Cn)

            ax = self.ax_pred; ax.clear(); self._style_plots()
            ax.plot(self.t, self.z, 'o', ms=3.5, label='Input points (ref)', zorder=4)
            ax.plot(tgrid, zfit_ref, '-', lw=2.0, label='Ref mathematical fit', zorder=3)
            ax.plot(self.t, z_pts_pred, 's', ms=3.0, label='Predicted points', zorder=2)
            ax.plot(tgrid, zfit_new, '-', lw=2.0, label='Predicted mathematical fit', zorder=1)
            ax.legend(loc='best'); self.canvas_pred.draw()

            # % errors
            zfit_on_pts = zth_from_foster_fit(self.t, self.Rf, self.Cf)
            rms_ref = float(np.sqrt(np.mean(((zfit_on_pts - self.z)/np.maximum(self.z,1e-12))**2)))
            dc_ref_err = abs(np.sum(self.Rf) - self.z[-1]) / max(self.z[-1],1e-12) * 100.0
            rms_new = float(np.sqrt(np.mean(((z_pts_pred - z_pts_pred)/np.maximum(z_pts_pred,1e-12))**2)))  # zero by construction
            dc_new_err = abs(np.sum(Rn) - z_pts_pred[-1]) / max(z_pts_pred[-1],1e-12) * 100.0
            self.txt_pred.insert('end', f'Ref: RMS {rms_ref*100:.3f}% | DC {dc_ref_err:.3f}%    ')
            self.txt_pred.insert('end', f'Pred: DC {dc_new_err:.3f}%\\n')
        except Exception as e:
            messagebox.showerror("Predict error", str(e))

if __name__ == '__main__':
    App().mainloop()
