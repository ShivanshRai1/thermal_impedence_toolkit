import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from utils_io import load_zth_csv
from zth_to_foster import fit_foster, zth_from_foster as zth_from_foster_fit
from foster_to_cauer import foster_to_cauer, zth_from_cauer
from thermal_predictor import scale_foster_by_area, zth_from_foster as zth_from_foster_predict

import csv
import os

def foster_time_curve(t, R, C):
    tau = np.asarray(R)*np.asarray(C)
    t = np.asarray(t, float)
    return (1.0 - np.exp(-np.outer(t, 1.0/np.maximum(tau, 1e-300)))) @ np.asarray(R)

def rms_percent(y_true, y_pred):
    y_true = np.asarray(y_true, float)
    y_pred = np.asarray(y_pred, float)
    if y_true.size == 0 or y_pred.size == 0:
        return np.nan
    err = y_true - y_pred
    rms = np.sqrt(np.mean(err * err))
    denom = max(np.max(np.abs(y_true)), 1e-12)
    return 100.0 * rms / denom

def dc_check_percent(zth_tail, R_sum):
    denom = max(abs(zth_tail), 1e-12)
    return 100.0 * abs(zth_tail - R_sum) / denom

def stringify_RC(R, C, indent="  "):
    lines = [f"(order={len(R)}):"]
    for i, (r, c) in enumerate(zip(R, C), 1):
        lines.append(f"{indent}{i:>2}: R = {r:.6g}, C = {c:.6g}")
    return "\n".join(lines)

def save_predicted_csv(tp, zth, parent):
    if tp is None or zth is None or len(tp) == 0:
        messagebox.showerror("Nothing to save", "No predicted data to save yet.")
        return
    path = filedialog.asksaveasfilename(
        parent=parent,
        title="Save predicted Zth vs tp as CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile="predicted_zth_vs_tp.csv"
    )
    if not path:
        return
    try:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["tp", "Zth"])
            for t, z in zip(tp, zth):
                w.writerow([t, z])
        messagebox.showinfo("Saved", f"Saved CSV:\n{path}")
    except Exception as e:
        messagebox.showerror("Save failed", str(e))

def _style_axes_loglog(ax):
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.grid(True, which='both', alpha=0.3)
    ax.set_xlabel('tp (s)')
    ax.set_ylabel('Zth (K/W)')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Thermal Impedance Toolkit")
        self.geometry("1220x820")
        self.minsize(1060, 720)
        self.t = self.z = None
        self.Rf = self.Cf = None
        self.Rc = self.Cc = None
        self.Rf_new = self.Cf_new = None
        self._build()

    def _build(self):
        # Left controls
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

        # Right: notebook
        right = ttk.Frame(self, padding=10); right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.nb = ttk.Notebook(right); self.nb.pack(fill=tk.BOTH, expand=True)

        # --- Fit → Foster ---
        self.tab_fit = ttk.Frame(self.nb); self.nb.add(self.tab_fit, text="Fit → Foster")
        fit_plot_frame = ttk.Frame(self.tab_fit); fit_plot_frame.pack(fill=tk.BOTH, expand=True)
        self.fig_fit = Figure(figsize=(6.6,4.2), dpi=100); self.ax_fit = self.fig_fit.add_subplot(111)
        _style_axes_loglog(self.ax_fit)
        self.canvas_fit = FigureCanvasTkAgg(self.fig_fit, master=fit_plot_frame)
        self.canvas_fit.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar_fit = NavigationToolbar2Tk(self.canvas_fit, fit_plot_frame, pack_toolbar=False)
        self.toolbar_fit.update(); self.toolbar_fit.pack(fill='x')

        fit_texts = ttk.Frame(self.tab_fit); fit_texts.pack(fill=tk.BOTH, expand=False, pady=(8,0))
        lf_rc = ttk.LabelFrame(fit_texts, text="Foster R, C values"); lf_rc.pack(side='left', fill='both', expand=True, padx=(0,6))
        self.txt_fit_rc = tk.Text(lf_rc, height=12, wrap='word'); self.txt_fit_rc.pack(fill='both', expand=True, padx=6, pady=6)
        lf_sc = ttk.LabelFrame(fit_texts, text="Sanity checks"); lf_sc.pack(side='left', fill='both', expand=True, padx=(6,0))
        self.txt_fit_checks = tk.Text(lf_sc, height=12, wrap='word'); self.txt_fit_checks.pack(fill='both', expand=True, padx=6, pady=6)

        # --- Foster → Cauer ---
        self.tab_cauer = ttk.Frame(self.nb); self.nb.add(self.tab_cauer, text="Foster → Cauer")
        cauer_plot_frame = ttk.Frame(self.tab_cauer); cauer_plot_frame.pack(fill=tk.BOTH, expand=True)
        self.fig_cauer = Figure(figsize=(6.6,4.2), dpi=100); self.ax_cauer = self.fig_cauer.add_subplot(111)
        _style_axes_loglog(self.ax_cauer)
        self.canvas_cauer = FigureCanvasTkAgg(self.fig_cauer, master=cauer_plot_frame)
        self.canvas_cauer.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar_cauer = NavigationToolbar2Tk(self.canvas_cauer, cauer_plot_frame, pack_toolbar=False)
        self.toolbar_cauer.update(); self.toolbar_cauer.pack(fill='x')

        # Only two panes as requested
        cauer_texts = ttk.Frame(self.tab_cauer); cauer_texts.pack(fill=tk.BOTH, expand=False, pady=(8,0))
        lf_crc = ttk.LabelFrame(cauer_texts, text="Cauer R, C values"); lf_crc.pack(side='left', fill='both', expand=True, padx=(0,6))
        self.txt_cauer_rc = tk.Text(lf_crc, height=12, wrap='word'); self.txt_cauer_rc.pack(fill='both', expand=True, padx=6, pady=6)
        lf_csc = ttk.LabelFrame(cauer_texts, text="Sanity checks"); lf_csc.pack(side='left', fill='both', expand=True, padx=(6,0))
        self.txt_cauer_checks = tk.Text(lf_csc, height=12, wrap='word'); self.txt_cauer_checks.pack(fill='both', expand=True, padx=6, pady=6)

        ttk.Button(self.tab_cauer, text="Convert Foster → Cauer", command=self._on_to_cauer).pack(anchor='e', pady=8, padx=6)

        # --- Predict Sibling ---
        self.tab_pred = ttk.Frame(self.nb); self.nb.add(self.tab_pred, text="Predict Sibling")
        pred_plot_frame = ttk.Frame(self.tab_pred); pred_plot_frame.pack(fill=tk.BOTH, expand=True)
        self.fig_pred = Figure(figsize=(6.6,4.2), dpi=100); self.ax_pred = self.fig_pred.add_subplot(111)
        _style_axes_loglog(self.ax_pred)
        self.canvas_pred = FigureCanvasTkAgg(self.fig_pred, master=pred_plot_frame)
        self.canvas_pred.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar_pred = NavigationToolbar2Tk(self.canvas_pred, pred_plot_frame, pack_toolbar=False)
        self.toolbar_pred.update(); self.toolbar_pred.pack(fill='x')

        pred_btns = ttk.Frame(self.tab_pred); pred_btns.pack(fill='x', pady=(8,0))
        ttk.Button(pred_btns, text="Predict", command=self._on_predict).pack(side='left', padx=(0,8))
        ttk.Button(pred_btns, text="Save as CSV", command=lambda: save_predicted_csv(self.tp_pred, self.zth_pred, self)).pack(side='left')
        self.txt_pred = tk.Text(self.tab_pred, height=6, wrap='word'); self.txt_pred.pack(fill='x', pady=(8,8))

        self._style_plots()

    def _style_plots(self):
        for ax in (self.ax_fit, self.ax_cauer, self.ax_pred):
            _style_axes_loglog(ax)

    def _on_load(self):
        path = filedialog.askopenfilename(filetypes=[("CSV","*.csv"),("All files","*.*")])
        if not path: return
        try:
            self.t, self.z = load_zth_csv(path)
            messagebox.showinfo("Loaded", f"Loaded {len(self.t)} points. Click 'Fit Foster'.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_fit_foster(self):
        for w in (self.txt_fit_rc, self.txt_fit_checks):
            w.configure(state="normal"); w.delete('1.0','end'); w.configure(state="normal")
        if self.t is None:
            messagebox.showerror("No data","Load CSV first."); return
        try:
            N = int(self.var_N.get())
            Rf, Cf, tau, zfit = fit_foster(self.t, self.z, N=N, refine_iters=2)
            self.Rf, self.Cf = Rf, Cf

            ax = self.ax_fit; ax.clear(); _style_axes_loglog(ax)
            ax.plot(self.t, self.z, 'o', ms=4, label='Input points', zorder=3)
            ax.plot(self.t, zfit, '-', lw=2.2, label='Mathematical fit (Foster)', zorder=2)
            ax.legend(loc='best'); self.canvas_fit.draw()

            dc_last = float(self.z[-1]); dc_sumR = float(np.sum(Rf))
            dc_err_pct = dc_check_percent(dc_last, dc_sumR)
            rms = rms_percent(self.z, zfit)

            self.txt_fit_rc.insert('end', stringify_RC(Rf, Cf))
            self.txt_fit_checks.insert('end', f"RMS error: {rms:.3f}%\n")
            self.txt_fit_checks.insert('end', f"DC check (tail Zth vs sum(R)): {dc_err_pct:.3f}%\n")
        except Exception as e:
            messagebox.showerror("Fit error", str(e))

    def _on_to_cauer(self):
        # Clear panes
        for w in (self.txt_cauer_rc, self.txt_cauer_checks):
            w.configure(state="normal"); w.delete('1.0','end'); w.configure(state="normal")
        if self.Rf is None or self.Cf is None:
            messagebox.showerror("No Foster","Fit Foster first."); return
        try:
            # Convert
            Rc, Cc = foster_to_cauer(self.Rf, self.Cf)
            self.Rc, self.Cc = Rc, Cc

            # Plot: Foster vs exact Cauer step response
            if self.t is not None:
                tmin = max(self.t.min(), 1e-9); tmax = self.t.max()
            else:
                tmin, tmax = 1e-9, 1.0
            tgrid = np.geomspace(tmin, tmax, 600)
            z_foster = zth_from_foster_fit(tgrid, self.Rf, self.Cf)
            z_cauer  = zth_from_cauer(tgrid, Rc, Cc)

            ax = self.ax_cauer; ax.clear(); _style_axes_loglog(ax)
            if self.t is not None and self.z is not None:
                ax.plot(self.t, self.z, 'o', ms=3.5, label='CSV points', zorder=4)
            ax.plot(tgrid, z_foster, '-', lw=2.0, label='Input (Foster)', zorder=3)
            ax.plot(tgrid, z_cauer,  '-', lw=2.0, label='Cauer step response', zorder=2)
            ax.legend(loc='best'); self.canvas_cauer.draw()

            # Fill panes
            self.txt_cauer_rc.insert('end', stringify_RC(Rc, Cc))
            dc_err = dc_check_percent(np.sum(self.Rf), np.sum(Rc))
            self.txt_cauer_checks.insert('end', f"DC equality (∑R Foster vs ∑R Cauer): {dc_err:.3f}%\n")
        except Exception as e:
            messagebox.showerror("Cauer error", str(e))

    def _on_predict(self):
        self.txt_pred.configure(state="normal"); self.txt_pred.delete('1.0','end'); self.txt_pred.configure(state="normal")
        if self.Rf is None:
            messagebox.showerror("No Foster","Fit Foster first."); return
        try:
            Aref = float(self.var_Aref.get())
            Anew_txt = self.var_Anew.get().strip()
            if not Anew_txt:
                messagebox.showinfo("Missing area","Enter New Die Area."); return
            Anew = float(Anew_txt)
            gam = float(self.var_gamma.get()) if self.gamma_mode.get()=='fixed' else 'blended'

            tgrid = np.geomspace(max(self.t.min(),1e-9), self.t.max(), 600)
            zfit_ref = foster_time_curve(tgrid, self.Rf, self.Cf)

            Rn, Cn, g = scale_foster_by_area(self.Rf, self.Cf, Aref, Anew, gamma=gam)
            self.Rf_new, self.Cf_new = Rn, Cn
            zfit_new = zth_from_foster_predict(tgrid, Rn, Cn)

            # Predicted points at original tp
            z_pts_pred = zth_from_foster_predict(self.t, Rn, Cn)

            ax = self.ax_pred; ax.clear(); _style_axes_loglog(ax)
            ax.plot(self.t, self.z, 'o', ms=3.5, label='Input points (ref)', zorder=4)
            ax.plot(tgrid, zfit_ref, '-', lw=2.0, label='Ref mathematical fit', zorder=3)
            ax.plot(self.t, z_pts_pred, 's', ms=3.0, label='Predicted points', zorder=2)
            ax.plot(tgrid, zfit_new, '-', lw=2.0, label='Predicted mathematical fit', zorder=1)
            ax.legend(loc='best'); self.canvas_pred.draw()

            # Metrics
            zfit_on_pts = zth_from_foster_fit(self.t, self.Rf, self.Cf)
            rms_ref = rms_percent(self.z, zfit_on_pts)
            dc_ref_err = dc_check_percent(self.z[-1], np.sum(self.Rf))
            dc_new_err = dc_check_percent(z_pts_pred[-1], np.sum(Rn))

            self.tp_pred, self.zth_pred = self.t, z_pts_pred

            self.txt_pred.insert('end', f"Ref: RMS {rms_ref:.3f}% | DC {dc_ref_err:.3f}%    ")
            self.txt_pred.insert('end', f"Pred: DC {dc_new_err:.3f}%\n")
            self.txt_pred.insert('end', "Use 'Save as CSV' to export predicted (tp, Zth).")
        except Exception as e:
            messagebox.showerror("Predict error", str(e))

if __name__ == '__main__':
    App().mainloop()
