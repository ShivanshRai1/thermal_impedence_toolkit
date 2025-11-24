# gui.py
# Basic Tkinter + Matplotlib GUI for Zth workflows:
# - Zth -> Foster fit (shows R,C + sanity checks)
# - Foster -> Cauer (shows both R,C + DC equality check)
# - Predict Sibling (4 curves + Save as CSV)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import csv
import os

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---- Project back-end imports (adjust names if your modules expose different APIs) ----
# EXPECTED:
#   fit_foster(tp, zth, order) -> (R_list, C_list, zth_fit) where zth_fit aligns with tp
#   foster_to_cauer(R_list, C_list) -> (Rc_list, Cc_list)
#   predict_sibling(tp, zth, area_ref, area_new, gamma) -> (tp_pred, zth_pred)
try:
    from zth_to_foster import fit_foster
except Exception:
    # Fallback shim (dev/testing): raises if actually called
    def fit_foster(tp, zth, order):
        raise RuntimeError("fit_foster(...) not found in zth_to_foster.py")

try:
    from foster_to_cauer import foster_to_cauer
except Exception:
    def foster_to_cauer(R, C):
        raise RuntimeError("foster_to_cauer(...) not found in foster_to_cauer.py")

try:
    from thermal_predictor import scale_foster_by_area, zth_from_foster as zth_from_foster_predict
except Exception:
    def predict_sibling(tp, zth, area_ref, area_new, gamma):
        raise RuntimeError("predict_sibling(...) not found in thermal_predictor.py")

# ---------------- Utility helpers ----------------

def read_csv_tp_zth(path):
    # Expects two columns: tp, Zth (with or without header)
    tp_vals, zth_vals = [], []
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # Try to skip header if non-numeric
    for r in rows:
        if not r:
            continue
        try:
            tp_vals.append(float(r[0]))
            zth_vals.append(float(r[1]))
        except ValueError:
            # Likely header row: skip
            continue
    if len(tp_vals) == 0:
        raise ValueError("No numeric data found. CSV must have two columns: tp, Zth.")
    # Sort by tp just in case
    tp = np.array(tp_vals, dtype=float)
    zth = np.array(zth_vals, dtype=float)
    idx = np.argsort(tp)
    return tp[idx], zth[idx]

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
    # DC Zth should equal sum(Ri)
    denom = max(abs(zth_tail), 1e-12)
    return 100.0 * abs(zth_tail - R_sum) / denom

def stringify_RC(label, R, C, indent="  "):
    lines = [f"{label} (order={len(R)}):"]
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

# ---------------- GUI ----------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zth Tools — Fit, Convert, Predict")
        self.geometry("1100x800")

        self._build_layout()

        # Data cache shared across tabs
        self.tp = None
        self.zth = None
        self.zth_fit = None
        self.foster_R = None
        self.foster_C = None

        # Prediction cache
        self.tp_pred = None
        self.zth_pred = None
        self.zth_pred_fit = None

    def _build_layout(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Tabs
        self.tab_fit = ttk.Frame(nb)
        self.tab_cauer = ttk.Frame(nb)
        self.tab_predict = ttk.Frame(nb)

        nb.add(self.tab_fit, text="Zth → Foster")
        nb.add(self.tab_cauer, text="Foster → Cauer")
        nb.add(self.tab_predict, text="Predict Sibling")

        # Build sub UIs
        self._build_fit_tab(self.tab_fit)
        self._build_cauer_tab(self.tab_cauer)
        self._build_predict_tab(self.tab_predict)

    # ---------- Tab 1: Zth -> Foster ----------
    def _build_fit_tab(self, root):
        # Top controls
        ctrl = ttk.Frame(root)
        ctrl.pack(fill="x", padx=8, pady=8)

        self.csv_path_var = tk.StringVar()
        ttk.Label(ctrl, text="CSV (tp, Zth):").pack(side="left")
        ttk.Entry(ctrl, textvariable=self.csv_path_var, width=60).pack(side="left", padx=6)
        ttk.Button(ctrl, text="Choose CSV", command=self._choose_csv).pack(side="left", padx=4)

        ttk.Label(ctrl, text="Order:").pack(side="left", padx=(16, 4))
        self.order_var = tk.IntVar(value=4)
        ttk.Spinbox(ctrl, from_=1, to=12, width=5, textvariable=self.order_var).pack(side="left")

        ttk.Button(ctrl, text="Fit → Foster", command=self._do_fit_foster).pack(side="left", padx=12)

        # Figure
        fig = Figure(figsize=(7.5, 4.6), dpi=100)
        self.ax_fit = fig.add_subplot(111)
        self.ax_fit.set_xlabel("tp (s)")
        self.ax_fit.set_ylabel("Zth (K/W)")
        self.ax_fit.grid(True, alpha=0.3)
        self.canvas_fit = FigureCanvasTkAgg(fig, master=root)
        self.canvas_fit.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=4)

        # Text output
        self.txt_fit = tk.Text(root, height=10, wrap="word")
        self.txt_fit.pack(fill="x", padx=8, pady=(0, 8))

    def _choose_csv(self):
        path = filedialog.askopenfilename(
            title="Choose CSV with tp,Zth",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        self.csv_path_var.set(path)

    def _do_fit_foster(self):
        path = self.csv_path_var.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Missing file", "Please choose a valid CSV file (tp, Zth).")
            return
        try:
            tp, zth = read_csv_tp_zth(path)
        except Exception as e:
            messagebox.showerror("CSV error", str(e))
            return

        order = max(1, int(self.order_var.get()))
        try:
            R, C, tau, zth_fit = fit_foster(tp, zth, N=order)
        except Exception as e:
            messagebox.showerror("Fit failed", f"fit_foster(...) raised:\n{e}")
            return

        # Cache
        self.tp, self.zth, self.zth_fit = tp, zth, zth_fit
        self.foster_R, self.foster_C = list(R), list(C)

        # Plot
        self.ax_fit.clear()
        self.ax_fit.grid(True, alpha=0.3)
        self.ax_fit.set_xlabel("tp (s)")
        self.ax_fit.set_ylabel("Zth (K/W)")
        self.ax_fit.plot(tp, zth, "o", ms=4, label="Input points")
        self.ax_fit.plot(tp, zth_fit, "-", lw=1.6, label="Foster fit")
        self.ax_fit.legend(loc="best")
        self.canvas_fit.draw()

        # Text (R,C + sanity checks)
        rms = rms_percent(zth, zth_fit)
        dc_err = dc_check_percent(zth[-1], np.sum(R))
        lines = []
        lines.append(stringify_RC("Foster R,C", R, C))
        lines.append("")
        lines.append("Sanity checks:")
        lines.append(f"  RMS error: {rms:.3f}%")
        lines.append(f"  DC check (tail Zth vs sum(R)): {dc_err:.3f}%")
        self._set_text(self.txt_fit, "\n".join(lines))

    # ---------- Tab 2: Foster -> Cauer ----------
    def _build_cauer_tab(self, root):
        # Controls
        ctrl = ttk.Frame(root)
        ctrl.pack(fill="x", padx=8, pady=8)

        ttk.Label(ctrl, text="Use Foster from previous fit or paste values below.").pack(side="left")
        ttk.Button(ctrl, text="Convert Foster → Cauer", command=self._do_foster_to_cauer).pack(side="right")

        # Figure (optional; we keep a small panel so layout matches)
        fig = Figure(figsize=(7.5, 3.8), dpi=100)
        self.ax_cauer = fig.add_subplot(111)
        self.ax_cauer.axis("off")
        self.canvas_cauer = FigureCanvasTkAgg(fig, master=root)
        self.canvas_cauer.get_tk_widget().pack(fill="both", expand=False, padx=8, pady=4)

        # Foster paste box
        paste_frame = ttk.Frame(root)
        paste_frame.pack(fill="x", padx=8, pady=(0, 4))

        ttk.Label(paste_frame, text="Foster R (comma/space-separated):").pack(anchor="w")
        self.entry_foster_R = tk.Text(paste_frame, height=3)
        self.entry_foster_R.pack(fill="x", pady=(0, 6))

        ttk.Label(paste_frame, text="Foster C (comma/space-separated):").pack(anchor="w")
        self.entry_foster_C = tk.Text(paste_frame, height=3)
        self.entry_foster_C.pack(fill="x", pady=(0, 6))

        # Text output (Foster & Cauer + sanity)
        self.txt_cauer = tk.Text(root, height=12, wrap="word")
        self.txt_cauer.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _parse_rc_textboxes_or_cache(self):
        # Try cache first
        if self.foster_R and self.foster_C:
            return list(self.foster_R), list(self.foster_C)

        # Fallback to pasted text
        def parse_txt(txt_widget):
            raw = txt_widget.get("1.0", "end").strip().replace("\n", " ")
            parts = [p for p in raw.replace(",", " ").split() if p]
            return [float(x) for x in parts]

        R, C = None, None
        try:
            R = parse_txt(self.entry_foster_R)
            C = parse_txt(self.entry_foster_C)
        except Exception:
            pass
        return R, C

    def _do_foster_to_cauer(self):
        R, C = self._parse_rc_textboxes_or_cache()
        if not R or not C or len(R) != len(C):
            messagebox.showerror("Invalid Foster", "Please provide valid Foster R and C of equal length (or run the Fit tab first).")
            return
        try:
            Rc, Cc = foster_to_cauer(R, C)
        except Exception as e:
            messagebox.showerror("Conversion failed", f"foster_to_cauer(...) raised:\n{e}")
            return

        # DC equality check
        dc_err = dc_check_percent(sum(R), sum(Rc))

        lines = []
        lines.append(stringify_RC("Foster R,C", R, C))
        lines.append("")
        lines.append(stringify_RC("Cauer  R,C", Rc, Cc))
        lines.append("")
        lines.append("Sanity checks:")
        lines.append(f"  DC equality (sum Foster R vs sum Cauer R): {dc_err:.3f}%")

        self._set_text(self.txt_cauer, "\n".join(lines))

        # Keep the text boxes in sync with what we used
        if not self.foster_R or not self.foster_C:
            self.foster_R, self.foster_C = list(R), list(C)

    # ---------- Tab 3: Predict Sibling ----------
    def _build_predict_tab(self, root):
        ctrl = ttk.Frame(root)
        ctrl.pack(fill="x", padx=8, pady=8)

        # Areas and gamma
        self.area_ref_var = tk.DoubleVar(value=1.0)
        self.area_new_var = tk.DoubleVar(value=1.0)
        self.gamma_var = tk.DoubleVar(value=1.0)

        ttk.Label(ctrl, text="Ref die area:").pack(side="left")
        ttk.Entry(ctrl, textvariable=self.area_ref_var, width=10).pack(side="left", padx=(4, 12))

        ttk.Label(ctrl, text="New die area:").pack(side="left")
        ttk.Entry(ctrl, textvariable=self.area_new_var, width=10).pack(side="left", padx=(4, 12))

        ttk.Label(ctrl, text="γ (gamma):").pack(side="left")
        ttk.Entry(ctrl, textvariable=self.gamma_var, width=10).pack(side="left", padx=(4, 12))

        ttk.Button(ctrl, text="Predict", command=self._do_predict).pack(side="left", padx=(8, 12))
        ttk.Button(ctrl, text="Save as CSV", command=lambda: save_predicted_csv(self.tp_pred, self.zth_pred, root)).pack(side="left")

        # Figure
        fig = Figure(figsize=(7.5, 4.6), dpi=100)
        self.ax_pred = fig.add_subplot(111)
        self.ax_pred.set_xlabel("tp (s)")
        self.ax_pred.set_ylabel("Zth (K/W)")
        self.ax_pred.grid(True, alpha=0.3)
        self.canvas_pred = FigureCanvasTkAgg(fig, master=root)
        self.canvas_pred.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=4)

        # Text output (reuse for any notes)
        self.txt_pred = tk.Text(root, height=8, wrap="word")
        self.txt_pred.pack(fill="x", padx=8, pady=(0, 8))

    def _do_predict(self):
        if self.tp is None or self.zth is None or self.foster_R is None or self.foster_C is None:
            messagebox.showerror("Missing source curve", "Run the Zth → Foster fit first.")
            return

        Aref = max(1e-12, float(self.area_ref_var.get()))
        Anew = max(1e-12, float(self.area_new_var.get()))
        gamma = float(self.gamma_var.get())  # numeric gamma

        # Scale Foster RC by area to get sibling’s Foster RC
        Rn, Cn, _ = scale_foster_by_area(self.foster_R, self.foster_C, Aref, Anew, gamma=gamma)

        # Predicted points on the original tp grid
        tp_pred = self.tp
        zth_pred = zth_from_foster_predict(tp_pred, Rn, Cn)

        # Optional: predicted "fit" curve via re-fit for overlay
        zth_pred_fit = None
        try:
            order = len(self.foster_R)
            _, _, _, zth_pred_fit = fit_foster(tp_pred, zth_pred, N=order)
        except Exception:
            pass

        self.tp_pred, self.zth_pred, self.zth_pred_fit = tp_pred, zth_pred, zth_pred_fit

        # Plot 4 curves
        self.ax_pred.clear()
        self.ax_pred.grid(True, alpha=0.3)
        self.ax_pred.set_xlabel("tp (s)"); self.ax_pred.set_ylabel("Zth (K/W)")
        self.ax_pred.plot(self.tp, self.zth, "o", ms=4, label="Input points")
        if self.zth_fit is not None:
            self.ax_pred.plot(self.tp, self.zth_fit, "-", lw=1.6, label="Input fit")
        self.ax_pred.plot(tp_pred, zth_pred, "o", ms=4, label="Predicted points")
        if zth_pred_fit is not None:
            self.ax_pred.plot(tp_pred, zth_pred_fit, "-", lw=1.6, label="Predicted fit")
        self.ax_pred.legend(loc="best")
        self.canvas_pred.draw()

        lines = []
        if self.zth_fit is not None:
            lines.append(f"Input fit RMS vs points: {rms_percent(self.zth, self.zth_fit):.3f}%")
        if zth_pred_fit is not None:
            lines.append(f"Predicted fit RMS vs predicted points: {rms_percent(zth_pred, zth_pred_fit):.3f}%")
        lines.append("Use 'Save as CSV' to export predicted (tp, Zth).")
        self._set_text(self.txt_pred, "\n".join(lines))


    # ---------- helpers ----------
    def _set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="normal")


if __name__ == "__main__":
    App().mainloop()
