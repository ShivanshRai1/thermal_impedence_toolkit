# app.py
# Minimal Flask backend to host the standalone HTML GUI and provide
# three endpoints used by the page:
#  - GET  /             -> serves index.html (placed alongside app.py)
#  - POST /api/fit_foster -> fits a Foster model (N terms) to provided Zth vs tp points
#  - POST /api/foster_to_cauer -> converts foster R,C arrays to Cauer ladder (simple placeholder)
#  - POST /api/predict -> predicts sibling/Zth scaled by area (and optional gamma blending)

from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
import numpy as np
from pathlib import Path

try:
    from scipy.optimize import least_squares
except Exception as e:
    least_squares = None

app = Flask(__name__, static_folder='.')
CORS(app)

# ----------------------------- helper math ---------------------------------

def _design_matrix(t, tau):
    """Compute design matrix Phi where Phi[i,j] = 1 - exp(-t[i]/tau[j])"""
    return 1.0 - np.exp(-np.outer(t, 1.0/np.maximum(tau, 1e-300)))

def _solve_R(t, z, tau):
    """Solve for R values given tau using linear least squares"""
    Phi = _design_matrix(t, tau)
    R, *_ = np.linalg.lstsq(Phi, z, rcond=None)
    return np.clip(R, 1e-18, None)

def _residual_tau(logtau, t, z):
    """Residual function for tau optimization"""
    tau = np.exp(logtau)
    R = _solve_R(t, z, tau)
    return _design_matrix(t, tau) @ R - z

def fit_foster(t, z, N=4, refine_iters=2):
    """
    Fit a Foster RC model to thermal impedance data.
    Uses two-step optimization: solve R given tau, then optimize tau iteratively.
    """
    t = np.asarray(t, float)
    z = np.asarray(z, float)
    
    if t.ndim != 1 or z.ndim != 1 or t.size != z.size or t.size < N:
        raise ValueError("Bad inputs or insufficient points")
    
    # Filter valid points
    mask = np.isfinite(t) & np.isfinite(z) & (t > 0)
    t = t[mask]
    z = z[mask]
    
    # Sort by time
    order = np.argsort(t)
    t = t[order]
    z = z[order]
    
    # Initialize tau values logarithmically
    tmin = max(np.min(t), 1e-9)
    tmax = np.max(t)
    tau = np.geomspace(tmin/5, tmax*5, N)
    
    # Initial R solve
    R = _solve_R(t, z, tau)
    
    # Iterative refinement
    for _ in range(refine_iters):
        if least_squares is not None:
            res = least_squares(_residual_tau, np.log(tau), args=(t, z))
            tau = np.exp(res.x)
        R = _solve_R(t, z, tau)
    
    # Compute C = tau / R
    C = tau / np.maximum(R, 1e-300)
    
    # Sort by tau
    idx = np.argsort(tau)
    R = R[idx]
    C = C[idx]
    tau = tau[idx]
    
    # Compute fitted curve
    zfit = _design_matrix(t, tau) @ R
    
    # Compute validation metrics
    rms_error = np.sqrt(np.mean((z - zfit) ** 2)) / (np.max(z) - np.min(z) + 1e-30) * 100
    dc_check = np.sum(R)
    dc_error = abs(dc_check - z[-1]) / (z[-1] + 1e-30) * 100
    
    return R, C, tau, zfit, z, t, rms_error, dc_error


# ----------------------------- API endpoints -------------------------------

@app.route('/')
def index():
    # Serve index.html (make sure index.html is in same directory as app.py)
    index_path = Path('index.html')
    if not index_path.exists():
        return "index.html not found. Place the standalone HTML (from the canvas) as index.html in this folder.", 404
    return send_from_directory('.', 'index.html')


@app.route('/api/fit_foster', methods=['POST'])
def api_fit_foster():
    data = request.get_json(force=True)
    points = data.get('points') or []
    N = int(data.get('N', 4))
    if len(points) < 3:
        return jsonify({'error': 'need at least 3 points to fit'}), 400

    tp = np.array([p.get('tp') for p in points], dtype=float)
    Zth = np.array([p.get('Zth') for p in points], dtype=float)

    try:
        R, C, tau, zfit, t_orig, z_orig, rms_error, dc_error = fit_foster(tp, Zth, N=N, refine_iters=2)
    except Exception as e:
        return jsonify({'error': 'Foster fitting failed', 'details': str(e)}), 500

    # Build response
    R = [float(r) for r in R]
    C = [float(c) for c in C]
    tau = [float(t) for t in tau]
    
    # Produce fitted series with smooth sampling
    t_sample = np.unique(np.concatenate((np.logspace(np.log10(t_orig.min()), np.log10(t_orig.max()), 200), t_orig)))
    zfit_sample = _design_matrix(t_sample, np.array(tau)) @ np.array(R)
    
    fit_series = [{'tp': float(t_sample[i]), 'Zth': float(zfit_sample[i])} for i in range(len(t_sample))]
    
    return jsonify({
        'R': R,
        'C': C,
        'tau': tau,
        'fitSeries': fit_series,
        'rms_error': float(rms_error),
        'dc_error': float(dc_error)
    })


@app.route('/api/foster_to_cauer', methods=['POST'])
def api_foster_to_cauer():
    # Very small placeholder: real Foster->Cauer conversion is more involved.
    data = request.get_json(force=True) or {}
    # expect R and C arrays or attempt to read from body
    R = data.get('R')
    C = data.get('C')
    if not R or not C:
        return jsonify({'warning': 'R and C not provided, returning empty conversion', 'R': [], 'C': []})
    # naive identity conversion (placeholder)
    return jsonify({'R_cauer': R, 'C_cauer': C, 'series': data.get('series', [])})


@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json(force=True)
    points = data.get('points') or []
    Aref = float(data.get('Aref', 1.0))
    Anew = float(data.get('Anew', 1.0))
    if len(points) < 1:
        return jsonify({'error': 'need at least one point'}), 400

    # simple area-scaling baseline (same as frontend fallback)
    scale = Aref / Anew if Anew!=0 else 1.0
    pred = [{'tp': float(p['tp']), 'Zth': float(p['Zth'] * scale)} for p in points]
    return jsonify({'scale': scale, 'series': pred, 'summary': f'simple area scale applied: {scale:.6f}'})


# ----------------------------- run server ---------------------------------
if __name__ == '__main__':
    print('Starting Flask server on http://127.0.0.1:5000 — serving index.html')
    app.run(debug=True)
