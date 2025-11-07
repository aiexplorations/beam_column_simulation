# Quick Start Guide 🚀

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Interactive Dashboard
```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501` and you'll see a beautiful dashboard with:
- **Left sidebar**: Sliders to adjust beam geometry, material, and loads
- **Main area**: Live FEA-style visualizations

### 3. Adjust Parameters
1. Set **beam length** (0.5-5 m)
2. Choose **cross-section** (width & height)
3. Select **material** (Steel/Aluminum/Wood/Concrete)
4. Apply **loads** (axial compression, lateral distributed, point)
5. Click **"Solve Problem"** to compute

### 4. Explore Results
- **Full Analysis tab**: 6-panel comprehensive FEA view
- **Simple View tab**: 4-panel quick overview
- **Data tab**: Export numerical results as CSV

---

## Run Pre-Made Examples

```bash
python test_simulator.py
```

This generates:
- `beam_column_comparison.png` - 4 different loading scenarios compared
- `beam_column_detailed.png` - Detailed 6-panel analysis

---

## Python API (No GUI)

For programmatic use:

```python
from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver
from visualizer import BeamVisualizer
import materials

# 1. Define geometry
section = BeamSection(width=0.1, height=0.1)  # 0.1m × 0.1m square section

# 2. Create problem
problem = BeamColumnProblem(
    length=2.0,                    # 2 meter beam
    section=section,
    material=materials.STEEL,      # E = 200 GPa
    axial_load=50000,              # 50 kN compression
    lateral_load=5000,             # 5 kN/m distributed
    point_load=5000                # 5 kN at free end
)

# 3. Solve
solver = BeamColumnSolver(problem)
x, v, M, V = solver.solve(num_points=100)

# 4. Calculate stresses
bending_stress, axial_stress, combined_stress = solver.calculate_stresses(x, M)

# 5. Calculate strains
bending_strain, axial_strain = solver.calculate_strains(bending_stress, axial_stress)

# 6. Visualize
visualizer = BeamVisualizer(
    problem, x, v, M, V,
    bending_stress, axial_stress,
    bending_strain, axial_strain
)

# Option A: Comprehensive 6-panel plot
fig = visualizer.create_comprehensive_plot()
fig.savefig('analysis.png', dpi=150, bbox_inches='tight')

# Option B: Simple 4-panel plot
fig = visualizer.create_simple_plot()

# Get key metrics
stats = visualizer.get_summary_stats()
print(f"Max deflection: {stats['max_deflection']*1000:.2f} mm")
print(f"Max stress: {stats['max_bending_stress']/1e6:.2f} MPa")
print(f"Max moment: {stats['max_moment']/1000:.2f} kN·m")
```

---

## What Each Parameter Does

| Parameter | Range | Effect |
|-----------|-------|--------|
| **Beam Length** | 0.5-5 m | Longer beams = more deflection |
| **Section Width** | 0.01-0.3 m | Wider section = more stiffness |
| **Section Height** | 0.01-0.3 m | Taller section = more stiffness (quadratic) |
| **Material** | 4 options | E modulus controls stiffness |
| **Axial Load** | 0-500 kN | Compression amplifies bending effects |
| **Lateral Load** | 0-100 kN/m | Perpendicular load causes bending |
| **Point Load** | 0-50 kN | Concentrated force at free end |

---

## Understanding the Visualizations

### Deflected Shape (Top Left)
- **X-axis**: Position along beam (m)
- **Y-axis**: Lateral deflection (m)
- **Color**: Stress intensity (red=high, blue=low)

### Heat Maps (Top Middle & Right)
- **X-axis**: Position along beam
- **Y-axis**: Distance from neutral axis
- **Color intensity**: Stress/strain magnitude
- Red zones = high stress (potential failure points)
- Blue zones = low stress

### Moment Diagram (Bottom Left)
- **Blue bars**: Positive bending moment (compression on top)
- **Red bars**: Negative bending moment
- **Magnitude**: Internal bending force

### Shear Diagram (Bottom Right)
- **Green line**: Internal shear force distribution
- **Steeper = higher shear gradient**

---

## Key Concepts

### Beam-Column Coupling
When axial load is high, deflection amplifies the bending moment, creating a **feedback effect**:
- No axial load → simple bending
- High compression → deflection creates larger moments → more deflection (**P-delta effect**)

### Stress Types
1. **Bending stress**: From moment M, varies across height
2. **Axial stress**: From compression P, constant across section
3. **Combined stress**: √(bending² + axial²)

### Material Stiffness
- **E (Young's modulus)** controls how much a material deforms
- **I (moment of inertia)** depends on geometry
- **EI (bending stiffness)** = resistance to bending

---

## Troubleshooting

**Dashboard not loading?**
```bash
streamlit run app.py --logger.level=debug
```

**Want to use different materials?**
Edit `materials.py` to add more options.

**Need different boundary conditions?**
Modify `BeamColumnSolver._beam_column_odes()` in `beam_column.py`

---

## Next Steps

1. **Play with sliders** in the Streamlit dashboard
2. **Compare materials** - see how aluminum deflects more than steel
3. **Observe coupling effect** - increase axial load and watch deflection amplify
4. **Export data** - download CSV and analyze in Excel/Python
5. **Modify the code** - add new materials, boundary conditions, or visualizations

Happy analyzing! 🏗️
