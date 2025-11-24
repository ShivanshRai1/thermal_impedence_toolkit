import numpy as np
from scipy.optimize import least_squares

def _design_matrix(t, tau):
    return 1.0 - np.exp(-np.outer(t, 1.0/np.maximum(tau,1e-300)))

def _solve_R(t,z,tau):
    Phi = _design_matrix(t,tau)
    R, *_ = np.linalg.lstsq(Phi,z,rcond=None)
    return np.clip(R,1e-18,None)

def _residual_tau(logtau,t,z):
    tau = np.exp(logtau)
    R = _solve_R(t,z,tau)
    return _design_matrix(t,tau)@R - z

def fit_foster(t,z,N=4,refine_iters=2):
    t=np.asarray(t,float); z=np.asarray(z,float)
    if t.ndim!=1 or z.ndim!=1 or t.size!=z.size or t.size<N:
        raise ValueError("Bad inputs or insufficient points")
    mask = np.isfinite(t) & np.isfinite(z) & (t>0)
    t=t[mask]; z=z[mask]
    order=np.argsort(t); t=t[order]; z=z[order]

    tmin=max(np.min(t),1e-9); tmax=np.max(t)
    tau=np.geomspace(tmin/5,tmax*5,N)
    R=_solve_R(t,z,tau)
    for _ in range(refine_iters):
        res=least_squares(_residual_tau,np.log(tau),args=(t,z))
        tau=np.exp(res.x); R=_solve_R(t,z,tau)
    C=tau/np.maximum(R,1e-300)
    idx=np.argsort(tau)
    R=R[idx]; C=C[idx]; tau=tau[idx]
    zfit = _design_matrix(t,tau)@R
    return R, C, tau, zfit

def zth_from_foster(t,R,C):
    tau=np.asarray(R)*np.asarray(C)
    return (1.0-np.exp(-np.outer(t,1.0/np.maximum(tau,1e-300))))@np.asarray(R)
