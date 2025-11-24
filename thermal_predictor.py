import numpy as np

def _blend_gamma(tau, tau_mid, width_dec=1.0, g_lo=0.5, g_hi=1.0):
    x = (np.log10(tau) - np.log10(tau_mid)) / max(width_dec, 1e-6)
    sig = 1.0/(1.0 + np.exp(-x))
    return g_lo*(1.0 - sig) + g_hi*sig

def scale_foster_by_area(R, C, A_ref, A_new, gamma='blended', tau_mid=None, width_dec=1.0):
    R = np.asarray(R, float); C = np.asarray(C, float)
    tau = R*C
    if A_ref <= 0 or A_new <= 0: raise ValueError("Areas must be positive")
    ratio = A_ref / A_new
    if isinstance(gamma, (int, float)):
        g = float(gamma) * np.ones_like(tau)
    elif gamma == 'blended':
        if tau_mid is None: tau_mid = np.sqrt(np.min(tau)*np.max(tau))
        g = _blend_gamma(tau, tau_mid, width_dec=width_dec, g_lo=0.5, g_hi=1.0)
    else:
        raise ValueError("gamma must be float or 'blended'")
    R_new = R * (ratio**g)
    C_new = C * (1.0/ratio)
    return R_new, C_new, g

def zth_from_foster(t, R, C):
    tau = np.asarray(R) * np.asarray(C)
    return (1.0 - np.exp(-np.outer(t, 1.0/np.maximum(tau, 1e-300)))) @ np.asarray(R)
