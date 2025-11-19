# Timoshenko Beam-Column Simulator

A modern web-based application for analyzing beam-column structures using Timoshenko beam theory with coupled nonlinear ODE solving and P-Δ effects.

## Overview

This application provides an interactive interface for analyzing the behavior of beams and columns under various loading conditions, including:

- **Timoshenko beam theory** - Accounts for shear deformation and rotary inertia
- **P-Δ effects** - Nonlinear geometric effects from axial loads
- **Multiple boundary conditions** - Cantilever, simply supported, fixed-fixed, and pinned-free
- **Point and distributed loads** - Custom load configurations
- **Material properties** - Steel, Aluminum, Wood, and Concrete
- **Interactive visualization** - Real-time 1:1 scale FEA-style deformation analysis

## Architecture

### Backend
- **Framework**: FastAPI (Python)
- **Port**: 8888
- **Physics Engine**: Custom ODE solver using the beam_column.py module
- **Features**:
  - RESTful API with Pydantic validation
  - CORS support for frontend communication
  - Material property database (4 materials)
  - Comprehensive solution output (deflections, moments, shears, stresses)

### Frontend
- **Pure HTML/CSS/JavaScript** - No build step required
- **Visualization**: Plotly.js for interactive scientific charts
- **State Management**: Client-side application state with parameter caching
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Features

### Input Controls (Sidebar)

**Geometry:**
- Beam Length: 0.5 - 5.0 m
- Section Width: 0.01 - 0.3 m
- Section Height: 0.01 - 0.3 m

**Material Selection:**
- Steel
- Aluminum
- Wood
- Concrete

**Beam Configuration:**
- Orientation: Horizontal / Vertical
- End Conditions:
  - Cantilever (Fixed-Free)
  - Simply Supported (Hinged-Hinged)
  - Fixed-Fixed
  - Hinged-Free (Pinned-Free)
- Self-Weight Toggle

**Applied Loads:**
- Axial Compressive Load: 0 - 500 kN
- Distributed Lateral Load: 0 - 100 kN/m
- Point Loads: Up to 5 loads at custom positions with directions

### Results Display

**Summary Metrics:**
- Maximum Deflection (mm)
- Maximum Stress (MPa)
- Maximum Moment (kN·m)
- Maximum Shear (kN)

**Charts Tab:**
- **FEA-Style Deflection Plot** (1:1 Scale)
  - Undeformed beam reference (dashed line)
  - Deformed shape with color fill
  - Cross-section rectangles at 5 key positions
  - Point load arrows showing magnitude and direction
  - Properly scaled for intuitive understanding

- **Bending Moment Diagram**
  - Moment distribution along beam length
  - Zero-line reference

- **Shear Force Diagram**
  - Shear distribution along beam length
  - Zero-line reference

- **Stress Distribution Heatmap**
  - 2D heatmap showing stress variation
  - Position along beam vs. height in section

**Summary Tab:**
- Complete problem parameters
- Solution results in tabular format

**Data Tab:**
- Position-by-position results table
- CSV export functionality
- Columns: Position, Deflection, Moment, Shear, Bending Stress, Axial Stress

## Default Configuration

The application loads with a default test case:
- **Beam**: 2.0 m steel beam, 0.1 × 0.1 m section
- **Orientation**: Horizontal with cantilever supports
- **Loads**:
  - Axial: 50 kN compressive
  - Distributed lateral: 10 kN/m
  - **Point loads** (default):
    - 25 kN downward at 0.2 L (20% of span)
    - 25 kN upward at 0.8 L (80% of span)
  - Self-weight: Included

## Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment (venv)
- Modern web browser

### Installation

1. **Set up virtual environment:**
```bash
cd /Users/rajesh/Github/beam_column_simulation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Install dependencies:**
```bash
pip install fastapi uvicorn
```

3. **Verify physics module:**
```bash
python -c "import sys; sys.path.append('physics'); from beam_column import *; print('Physics module loaded')"
```

### Running the Application

1. **Start the backend (in terminal 1):**
```bash
source venv/bin/activate
python backend/main.py
```

The backend will start on `http://localhost:8888`

2. **Open the frontend (in web browser):**
```
Open index.html in your default browser
or
Visit: file:///Users/rajesh/Github/beam_column_simulation/frontend/index.html
```

### Verification

Test the backend health:
```bash
curl http://localhost:8888/health
```

Expected response:
```json
{"status": "healthy"}
```

## File Structure

```
beam_column_simulation/
├── README.md                 # Documentation
├── launch.sh                 # Launch script
├── requirements.txt          # Python dependencies
├── backend/
│   └── main.py              # FastAPI backend server
├── physics/
│   ├── beam_column.py       # Physics solver module
│   ├── visualizer.py        # Visualization utilities
│   └── materials.py         # Material definitions
├── frontend/
│   ├── index.html           # Main frontend HTML
│   ├── js/
│   │   ├── api.js           # Backend API client
│   │   ├── state.js         # Application state management
│   │   ├── ui.js            # UI rendering and charts
│   │   └── main.js          # Application initialization
│   └── css/
│       └── style.css        # Responsive styling
└── [demo scripts]           # Various analysis examples
```

## API Reference

### Health Check
```
GET /health
```
Returns server status.

### Get Materials
```
GET /api/materials
```
Returns available materials with properties (E, ρ, σ_y).

### Solve Problem
```
POST /api/solve
Content-Type: application/json
```

**Request Body:**
```json
{
  "length": 2.0,
  "width": 0.1,
  "height": 0.1,
  "material": "Steel",
  "orientation": "horizontal",
  "end_condition": "cantilever",
  "axial_load": 50,
  "lateral_load": 10,
  "include_self_weight": true,
  "point_loads": [
    {"magnitude": 25, "position": 0.2, "direction": "downward"},
    {"magnitude": 25, "position": 0.8, "direction": "upward"}
  ]
}
```

**Response:**
```json
{
  "data": {
    "x": [0, 0.02, 0.04, ...],
    "deflection": [0, -0.0001, -0.0003, ...],
    "moment": [100, 95, 85, ...],
    "shear": [50, 49.5, 48.9, ...],
    "bending_stress": [150, 145, 140, ...],
    "axial_stress": [500, 500, 500, ...]
  },
  "summary": {
    "max_deflection_mm": 4.30,
    "max_bending_stress_mpa": 120.0,
    "max_moment_knm": 10.70,
    "max_shear_kn": 20.76
  }
}
```

## Visualization Details

### 1:1 Scale Deflection Plot

The FEA-style deflection visualization uses equal aspect ratio (1:1 scale) on both axes:

- **Scaling Factor**: Max deflection is automatically scaled to approximately 15% of beam length for visibility
- **Cross-sections**: 5 red rectangles show the beam cross-section at key positions
- **Point loads**: Colored arrows indicate load positions and directions
  - Orange arrows: Downward loads
  - Purple arrows: Upward loads
- **Deformed shape**: Blue filled area shows actual deformed shape from ODE solver

### Orientation Handling

**Horizontal beams:**
- X-axis: Position along beam (m)
- Y-axis: Vertical deflection (mm)
- Point loads shown as vertical arrows

**Vertical beams:**
- X-axis: Horizontal deflection (mm)
- Y-axis: Height along beam (m)
- Point loads shown as horizontal arrows

## Testing

Run the backend test suite:

```bash
source venv/bin/activate
python << 'EOF'
import sys
sys.path.insert(0, '/Users/rajesh/Github/beam_column_simulation')
from backend import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test health
response = client.get('/health')
assert response.status_code == 200
print('✓ Health check passed')

# Test materials
response = client.get('/api/materials')
assert response.status_code == 200
assert len(response.json()['materials']) == 4
print('✓ Materials endpoint passed')

# Test solve
payload = {
    'length': 2.0,
    'width': 0.1,
    'height': 0.1,
    'material': 'Steel',
    'orientation': 'horizontal',
    'end_condition': 'cantilever',
    'axial_load': 50,
    'lateral_load': 10,
    'include_self_weight': True,
    'point_loads': [
        {'magnitude': 25.0, 'position': 0.2, 'direction': 'downward'},
        {'magnitude': 25.0, 'position': 0.8, 'direction': 'upward'}
    ]
}
response = client.post('/api/solve', json=payload)
assert response.status_code == 200
print('✓ Solve endpoint passed')

print('\nAll tests passed!')
EOF
```

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires support for:
- ES6 JavaScript
- Plotly.js
- CSS Grid and Flexbox

## Performance Notes

- **Initial load**: < 2 seconds
- **Solve operation**: 100-500 ms depending on beam complexity
- **Chart rendering**: < 1 second with Plotly.js

## Troubleshooting

### Backend won't start
```bash
# Check if port is in use
lsof -i :8888
# If in use, kill and retry
kill -9 <PID>
python backend.py 8888
```

### Frontend shows "API connection failed"
- Verify backend is running: `curl http://localhost:8888/health`
- Check browser console for CORS errors
- Ensure port 8888 matches in index.html

### Charts not rendering
- Check browser console for Plotly.js errors
- Verify Plotly CDN is accessible
- Try clearing browser cache

## Future Enhancements

Potential improvements:
1. 3D visualization of deformed shape
2. Dynamic response analysis
3. Buckling analysis and critical load
4. Composite beam support
5. Temperature effects
6. Parametric studies and optimization
7. Export to FEA formats (STEP, IGES)

---

**Application Version**: 1.0
**Last Updated**: November 2024
**Physics Engine**: Timoshenko Beam Theory with P-Δ Effects
