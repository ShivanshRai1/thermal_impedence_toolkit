import numpy as np
from dataclasses import dataclass
from typing import Tuple
from scipy.optimize import least_squares
from scipy.linalg import eig, inv

@dataclass
class FosterRC:
    R: np.ndarray
    C: np.ndarray

@dataclass
class CauerRC:
    R: np.ndarray
    C: np.ndarray

def foster_impedance(jw: np.ndarray, foster: FosterRC) -> np.ndarray:
    R, C = foster.R, foster.C
    Z = np.zeros_like(jw, dtype=complex)
    for Ri, Ci in zip(R, C):
        Z += Ri / (1.0 + jw * Ri * Ci)
    return Z

def cauer_impedance(jw: np.ndarray, cauer: CauerRC) -> np.ndarray:
    R, C = cauer.R, cauer.C
    Z = None
    for k in reversed(range(len(R))):
        if Z is None:
            Z = R[k] + 1.0 / (jw * C[k])
        else:
            Z = R[k] + 1.0 / (jw * C[k] + 1.0 / Z)
    return Z

def foster_to_cauer(R_foster: np.ndarray, C_foster: np.ndarray, n_freq: int = 400) -> Tuple[np.ndarray, np.ndarray]:
    R_foster = np.asarray(R_foster, float).ravel()
    C_foster = np.asarray(C_foster, float).ravel()
    if R_foster.size != C_foster.size or R_foster.size < 1:
        raise ValueError("R and C must match and be non-empty")
    if not np.all(R_foster>0) or not np.all(C_foster>0):
        raise ValueError("Foster R,C must be positive")
    n = R_foster.size

    taus = R_foster * C_foster
    wmin = 0.1 / (taus.max() * 50.0)
    wmax = 10.0 / (taus.min() * 0.02)
    w = np.logspace(np.log10(wmin), np.log10(wmax), n_freq)
    jw = 1j * w

    foster = FosterRC(R=R_foster, C=C_foster)
    Zt = foster_impedance(jw, foster)

    Rtot = Zt[0].real if np.isfinite(Zt[0].real) and Zt[0].real>0 else float(np.sum(R_foster))
    R0 = np.full(n, Rtot/(1.8*n))
    taper = np.linspace(1.3,0.7,n); R0 *= taper; R0 *= (Rtot/max(R0.sum(),1e-12))
    order = np.argsort(taus)
    C0 = C_foster[order].copy()
    x0 = np.hstack([np.maximum(R0,1e-12), np.maximum(C0,1e-12)])
    lb = np.hstack([np.full(n,1e-12), np.full(n,1e-12)])
    ub = np.hstack([np.full(n,np.inf), np.full(n,np.inf)])

    def pack(x): return x[:n], x[n:]
    def residual(x):
        Rc, Cc = pack(x)
        Zc = cauer_impedance(jw, CauerRC(R=Rc, C=Cc))
        mag_err = (np.abs(Zc) - np.abs(Zt)) / np.maximum(np.abs(Zt), 1e-12)
        ang_err = (np.angle(Zc) - np.angle(Zt))
        return np.hstack([mag_err, 0.3*ang_err])

    sol = least_squares(residual, x0, bounds=(lb,ub), xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=8000)
    Rc, Cc = pack(sol.x)

    # enforce DC equality exactly
    if np.sum(Rc) > 0:
        Rc *= (Zt[0].real / np.sum(Rc))

    return Rc, Cc

# --- NEW: exact time-domain step response for a Cauer ladder ---
def zth_from_cauer(t, R, C):
    """
    Zth(t) for a Cauer ladder with series R and shunt C at each node.
    Nodes: 0..n-1 have capacitances C[i]; series resistors R[i] connect
    node (i-1) to i, with the last R[n-1] connecting node n-1 to ground (ambient).
    Unit power step is modeled as a 1 A current source into node 0.
    Returns Zth evaluated at times t (array-like).
    """
    R = np.asarray(R, float).ravel()
    C = np.asarray(C, float).ravel()
    t = np.asarray(t, float).ravel()
    n = R.size
    if n == 0:
        return np.zeros_like(t, float)
    if C.size != n:
        raise ValueError("R and C must be same length")
    if not np.all(R>0) or not np.all(C>0):
        raise ValueError("R,C must be positive")

    # Build conductance matrix G (NxN) with last resistor to ground
    G = np.zeros((n, n), float)
    g = 1.0 / np.maximum(R, 1e-300)
    # Resistances between node i and i+1 for i=0..n-2
    for i in range(n-1):
        gi = g[i]
        G[i, i] += gi
        G[i+1, i+1] += gi
        G[i, i+1] -= gi
        G[i+1, i] -= gi
    # Last resistor from node n-1 to ground
    G[n-1, n-1] += g[n-1]

    # Capacitance matrix (diagonal)
    Cmat = np.diag(C)

    # DC solution V_inf solves G V = e0 (unit current at node 0)
    e0 = np.zeros(n, float); e0[0] = 1.0
    V_inf = np.linalg.solve(G, e0)

    # State matrix A = C^{-1} G
    Cinv = np.diag(1.0 / np.maximum(C, 1e-300))
    A = Cinv @ G

    # Modal decomposition for fast exp(-A t) action
    # A = V * diag(w) * V^{-1}
    w, V = eig(A)                   # w: eigenvalues, V: right eigenvectors
    Vinv = inv(V)
    y0 = Vinv @ V_inf               # constant vector in modal coordinates

    # V(t) = V_inf - V * (exp(-w*t) ∘ y0)
    # Evaluate at all t using broadcasting
    exp_terms = np.exp(-np.outer(w, t)) * y0[:, None]   # shape (n, len(t))
    Vt = V_inf[:, None] - (V @ exp_terms)
    zth = Vt[0, :].real
    return zth
