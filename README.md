<<<<<<< HEAD
# Thermal Impedance Toolkit (v3)

This GUI lets you:
1) Fit Foster RC to Zth(t) CSV (points + *mathematical fit* curve shown together).
2) Convert Foster → same‑order Cauer and visualize equivalence (points + *mathematical fit* curve).
3) Predict sibling package (area + gamma) and show 4 curves:
   - input points (ref), ref mathematical fit, predicted points, predicted mathematical fit.

It also prints percentage errors (RMS %, DC %, DC equality %).

## Run
```bash
pip install -r requirements.txt
python gui.py
```

## CSV
Two columns: `t_seconds, Zth_K_per_W`. Times must be >0.
=======
# thermal_impedence_toolkit
>>>>>>> 9c6e8bfacf69ff54600084385bc49dc8db3d330d
