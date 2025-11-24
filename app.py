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
    from scipy.optimize import curve_fit
except Exception as e:
    curve_fit = None

app = Flask(__name__, static_folder='.')
CORS(app)

# ----------------------------- helper math ---------------------------------

def foster_model(t, *params):
    # params is [A1, tau1, A2, tau2, ...] where Ai = R_i, tau_i = R_i*C_i
    # Z(t) = sum_i A_i * (1 - exp(-t / tau_i))
    t = np.asarray(t)
    Z = np.zeros_like(t, dtype=float)
    for i in range(0, len(params), 2):
        A = params[i]
        tau = params[i+1]
        Z += A * (1.0 - np.exp(-t / np.maximum(tau, 1e-30)))
    return Z


def initial_guess_for_foster(t, Z, N):
    # simple heuristic: spread taus logarithmically between min and max t
    t = np.asarray(t)
    tmin = max(t.min(), 1e-12)
    tmax = max(t.max(), tmin*1e6)
    taus = np.logspace(np.log10(tmin), np.log10(tmax), N)
    # amplitude guesses: split final Z by N
    Zfinal = Z[-1] if len(Z) else 1.0
    As = np.full(N, Zfinal / N)
    params = []
    for A, tau in zip(As, taus):
        params.extend([float(A), float(tau)])
    return params


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
    Z = np.array([p.get('Zth') for p in points], dtype=float)

    # sort
    order = np.argsort(tp)
    tp = tp[order]
    Z = Z[order]

    if curve_fit is None:
        # SciPy not installed: return a simple heuristic decomposition
        params = initial_guess_for_foster(tp, Z, N)
        R = [params[i] for i in range(0,len(params),2)]
        tau = [params[i+1] for i in range(0,len(params),2)]
        C = [tau[i] / max(R[i], 1e-30) for i in range(len(R))]
        return jsonify({'warning': 'scipy.optimize.curve_fit not available; returned heuristic split',
                        'R': R, 'C': C, 'fitSeries': [{'tp': float(tp[i]), 'Zth': float(Z[i])} for i in range(len(tp))]})

    # perform nonlinear least squares
    p0 = initial_guess_for_foster(tp, Z, N)
    try:
        popt, pcov = curve_fit(foster_model, tp, Z, p0=p0, maxfev=20000)
    except Exception as e:
        return jsonify({'error': 'curve_fit failed', 'details': str(e)}), 500

    # parse parameters
    R = [float(popt[i]) for i in range(0,len(popt),2)]
    tau = [float(popt[i+1]) for i in range(0,len(popt),2)]
    C = [tau[i] / max(R[i], 1e-30) for i in range(len(R))]

    # produce fitted series (sampled)
    t_sample = np.unique(np.concatenate((np.linspace(tp.min(), tp.max(), 200), tp)))
    Z_fit = foster_model(t_sample, *popt)
    fit_series = [{'tp': float(t_sample[i]), 'Zth': float(Z_fit[i])} for i in range(len(t_sample))]

    return jsonify({'R': R, 'C': C, 'fitSeries': fit_series})


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
