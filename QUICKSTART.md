# Quick Start Guide

## Running the Thermal Impedance Toolkit React App

Follow these steps to get the application running:

### 1. Install Frontend Dependencies

Open PowerShell in the `frontend` directory and run:

```powershell
cd "c:\Users\Dragon Byte\Downloads\thermal_impedance_toolkit_v9\frontend"
npm install
```

This will install all required packages (React, Vite, Recharts, etc.).

### 2. Start the Flask Backend

Open a **NEW** PowerShell window and run:

```powershell
cd "c:\Users\Dragon Byte\Downloads\thermal_impedance_toolkit_v9"
python app.py
```

You should see:
```
Starting Flask server on http://127.0.0.1:5000 — serving index.html
```

**Keep this window open** - the Flask server must stay running.

### 3. Start the React Frontend

In the **first** PowerShell window (in the `frontend` directory), run:

```powershell
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  press h to show help
```

### 4. Open in Browser

Open your web browser and go to:
```
http://localhost:3000
```

You should see the Thermal Impedance Toolkit interface!

## How to Use

1. **Upload CSV** - Click "Choose File" and select a CSV with `tp` and `Zth` columns
2. **Fit Foster** - Click the blue "Fit Foster" button to generate RC model
3. **View Results** - See the fitted curve and R/C values in the table
4. **Convert to Cauer** - Switch to "Foster → Cauer" tab and click "Convert to Cauer"
5. **Predict Sibling** - Enter a new die area and click "Predict Sibling"

## Stopping the Application

- **Frontend**: Press `Ctrl+C` in the PowerShell window running `npm run dev`
- **Backend**: Press `Ctrl+C` in the PowerShell window running `python app.py`

## Troubleshooting

### "npm: command not found"
- Install Node.js from https://nodejs.org/
- Restart PowerShell after installation

### "Port 3000 is already in use"
- Close any other applications using port 3000
- Or change the port in `vite.config.js`

### CSV not loading
- Ensure CSV has columns named `tp` or `t` for time
- Ensure CSV has columns named `Zth` or `Z` for impedance
- Column names are case-insensitive

### API errors
- Make sure Flask backend is running on port 5000
- Check that both servers are running simultaneously
