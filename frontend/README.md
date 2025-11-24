# Thermal Impedance Toolkit - React Frontend

Modern React + JavaScript web application for thermal impedance analysis.

## Features

- **CSV Upload** - Parse thermal impedance data (tp, Zth columns)
- **Foster Fitting** - Fit RC network models to thermal data
- **Cauer Conversion** - Convert Foster to Cauer representations
- **Sibling Prediction** - Predict thermal behavior for different package sizes
- **Interactive Charts** - Visualize data with Recharts
- **Real-time Updates** - Responsive UI with instant feedback

## Tech Stack

- **React 18** - Component-based UI framework
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Recharts** - React charting library
- **Axios** - HTTP client for API calls
- **PapaParse** - CSV parsing

## Setup & Installation

### Prerequisites

- Node.js 16+ installed
- Python Flask backend running (see parent directory)

### Installation Steps

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   ```
   http://localhost:3000
   ```

## Running the Full Application

### Step 1: Start Flask Backend

In the parent directory (`thermal_impedance_toolkit_v9`):

```bash
# Install Python dependencies (if not done)
pip install --user -r requirements.txt

# Start Flask server
python app.py
```

Flask will run on `http://localhost:5000`

### Step 2: Start React Frontend

In this directory (`frontend`):

```bash
npm run dev
```

React will run on `http://localhost:3000` and proxy API calls to Flask.

### Step 3: Use the Application

1. Open `http://localhost:3000` in your browser
2. Upload a CSV file with `tp` (time) and `Zth` (thermal impedance) columns
3. Click "Fit Foster" to generate RC model
4. Switch to other tabs for Cauer conversion or sibling prediction

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload.jsx        # CSV file upload
│   │   ├── Sidebar.jsx           # Input controls
│   │   ├── ResultChart.jsx       # Recharts wrapper
│   │   ├── FitFosterTab.jsx      # Foster fitting UI
│   │   ├── FosterToCauerTab.jsx  # Cauer conversion UI
│   │   └── PredictSiblingTab.jsx # Sibling prediction UI
│   ├── hooks/
│   │   ├── useApi.js             # Flask API integration
│   │   └── useCsvParser.js       # CSV parsing logic
│   ├── context/
│   │   └── DataContext.jsx       # Global state management
│   ├── App.jsx                   # Main app component
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Tailwind CSS
├── index.html
├── vite.config.js                # Vite configuration
├── package.json
└── README.md
```

## API Endpoints (Proxied to Flask)

- `POST /api/fit_foster` - Fit Foster RC model
- `POST /api/foster_to_cauer` - Convert Foster to Cauer
- `POST /api/predict` - Predict sibling package

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## Troubleshooting

### Port 3000 already in use
Change the port in `vite.config.js`:
```js
server: {
  port: 3001  // or any other port
}
```

### API calls failing
- Ensure Flask backend is running on port 5000
- Check browser console for CORS errors
- Verify `vite.config.js` proxy settings

### CSV not parsing
- Ensure CSV has columns named `tp`/`t` and `Zth`/`Z` (case-insensitive)
- Check that time values are positive numbers
- Verify CSV is properly formatted

## Development

### Adding new features

1. Create new component in `src/components/`
2. Add to `App.jsx` if it's a new tab
3. Update `DataContext.jsx` if new state is needed
4. Add API call to `useApi.js` if backend integration required

### Styling

This project uses Tailwind CSS. Modify `tailwind.config.js` to customize theme.

## License

MIT
