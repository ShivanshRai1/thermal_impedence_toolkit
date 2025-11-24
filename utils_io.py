import numpy as np

def load_zth_csv(path):
    data = np.genfromtxt(path, delimiter=',', dtype=float)
    if data.ndim == 1 or data.shape[1] < 2:
        raise ValueError("CSV must have at least two columns: time, Zth")
    t = data[:,0].astype(float)
    z = data[:,1].astype(float)
    mask = np.isfinite(t) & np.isfinite(z)
    t = t[mask]; z = z[mask]
    order = np.argsort(t)
    t = t[order]; z = z[order]
    keep = (t>0) & (np.concatenate([[True], np.diff(t)>0]))
    return t[keep], z[keep]

def save_rc_csv(path, R, C, header='R,C'):
    import csv
    with open(path,'w',newline='') as f:
        w=csv.writer(f); w.writerow(header.split(','))
        for r,c in zip(R,C): w.writerow([r,c])
