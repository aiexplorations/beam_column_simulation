"""
Demo script showcasing visual representations of vertical vs horizontal beams.
"""

import numpy as np
import matplotlib.pyplot as plt
from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver
from visualizer import BeamVisualizer
import materials


def create_side_by_side_visualization():
    """Create side-by-side visualization of horizontal and vertical beams."""

    section = BeamSection(width=0.08, height=0.15)

    # Horizontal beam
    problem_h = BeamColumnProblem(
        length=2.5,
        section=section,
        material=materials.STEEL,
        axial_load=30000,
        lateral_load=8000,
        point_load=0,
        orientation="horizontal",
        include_self_weight=True
    )

    # Vertical beam with self-weight
    problem_v = BeamColumnProblem(
        length=2.5,
        section=section,
        material=materials.STEEL,
        axial_load=30000,
        lateral_load=8000,
        point_load=0,
        orientation="vertical",
        include_self_weight=True
    )

    # Solve both
    print("Solving horizontal beam...")
    solver_h = BeamColumnSolver(problem_h)
    x_h, v_h, M_h, V_h = solver_h.solve(num_points=100)
    b_stress_h, a_stress_h, _ = solver_h.calculate_stresses(x_h, M_h)
    b_strain_h, a_strain_h = solver_h.calculate_strains(b_stress_h, a_stress_h)

    print("Solving vertical beam...")
    solver_v = BeamColumnSolver(problem_v)
    x_v, v_v, M_v, V_v = solver_v.solve(num_points=100)
    b_stress_v, a_stress_v, _ = solver_v.calculate_stresses(x_v, M_v)
    b_strain_v, a_strain_v = solver_v.calculate_strains(b_stress_v, a_stress_v)

    # Create visualizers
    viz_h = BeamVisualizer(problem_h, x_h, v_h, M_h, V_h, b_stress_h, a_stress_h, b_strain_h, a_strain_h)
    viz_v = BeamVisualizer(problem_v, x_v, v_v, M_v, V_v, b_stress_v, a_stress_v, b_strain_v, a_strain_v)

    # Create figure with two simple plots side by side
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle("Beam Orientation Visualization: Horizontal vs Vertical", fontsize=16, fontweight='bold')

    # Horizontal beam plots
    ax1 = plt.subplot(2, 3, 1)
    norm_h = plt.Normalize(vmin=0, vmax=np.max(b_stress_h))
    cmap_h = plt.cm.hot
    scatter1 = ax1.scatter(x_h, v_h, c=b_stress_h, cmap=cmap_h, s=50)
    ax1.plot(x_h, v_h, 'k-', linewidth=2)
    ax1.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    ax1.set_xlabel("Position (m)", fontsize=11)
    ax1.set_ylabel("Vertical Deflection (m)", fontsize=11)
    ax1.set_title("HORIZONTAL BEAM\nDeflected Shape with Stress", fontweight='bold', fontsize=12)
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label("Stress (Pa)")

    # Horizontal moment diagram
    ax2 = plt.subplot(2, 3, 2)
    ax2.fill_between(x_h, M_h/1000, alpha=0.5, color='blue')
    ax2.plot(x_h, M_h/1000, 'b-', linewidth=2)
    ax2.axhline(y=0, color='k', linewidth=1)
    ax2.set_xlabel("Position (m)", fontsize=11)
    ax2.set_ylabel("Moment (kN·m)", fontsize=11)
    ax2.set_title("HORIZONTAL BEAM\nBending Moment Diagram", fontweight='bold', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')

    # Horizontal stress distribution
    ax3 = plt.subplot(2, 3, 3)
    ax3.fill_between(x_h, b_stress_h/1e6, alpha=0.5, color='red')
    ax3.plot(x_h, b_stress_h/1e6, 'r-', linewidth=2)
    ax3.set_xlabel("Position (m)", fontsize=11)
    ax3.set_ylabel("Bending Stress (MPa)", fontsize=11)
    ax3.set_title("HORIZONTAL BEAM\nBending Stress Distribution", fontweight='bold', fontsize=12)
    ax3.grid(True, alpha=0.3)

    # Vertical beam plots
    ax4 = plt.subplot(2, 3, 4)
    norm_v = plt.Normalize(vmin=0, vmax=np.max(b_stress_v))
    cmap_v = plt.cm.hot
    scatter4 = ax4.scatter(v_v, x_v, c=b_stress_v, cmap=cmap_v, s=50)
    ax4.plot(v_v, x_v, 'k-', linewidth=2)
    ax4.axvline(x=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    # Gravity arrow
    ax4.arrow(np.min(v_v)*0.7, x_v[-1]*0.85, 0, -0.3,
             head_width=0.005, head_length=0.08, fc='red', ec='red', linewidth=2, alpha=0.8)
    ax4.text(np.min(v_v)*0.7 + 0.01, x_v[-1]*0.8, 'Gravity', fontsize=10, color='red', fontweight='bold')
    ax4.set_xlabel("Lateral Deflection (m)", fontsize=11)
    ax4.set_ylabel("Height (m)", fontsize=11)
    ax4.set_title("VERTICAL BEAM\nDeflected Shape with Stress", fontweight='bold', fontsize=12)
    ax4.grid(True, alpha=0.3)
    cbar4 = plt.colorbar(scatter4, ax=ax4)
    cbar4.set_label("Stress (Pa)")

    # Vertical moment diagram
    ax5 = plt.subplot(2, 3, 5)
    ax5.fill_between(x_v, M_v/1000, alpha=0.5, color='blue')
    ax5.plot(x_v, M_v/1000, 'b-', linewidth=2)
    ax5.axhline(y=0, color='k', linewidth=1)
    ax5.set_xlabel("Height (m)", fontsize=11)
    ax5.set_ylabel("Moment (kN·m)", fontsize=11)
    ax5.set_title("VERTICAL BEAM\nBending Moment Diagram", fontweight='bold', fontsize=12)
    ax5.grid(True, alpha=0.3, axis='y')

    # Vertical stress distribution
    ax6 = plt.subplot(2, 3, 6)
    ax6.fill_between(x_v, b_stress_v/1e6, alpha=0.5, color='red')
    ax6.plot(x_v, b_stress_v/1e6, 'r-', linewidth=2)
    ax6.set_xlabel("Height (m)", fontsize=11)
    ax6.set_ylabel("Bending Stress (MPa)", fontsize=11)
    ax6.set_title("VERTICAL BEAM\nBending Stress Distribution", fontweight='bold', fontsize=12)
    ax6.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('visualization_orientation_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: visualization_orientation_comparison.png")

    # Print comparison
    stats_h = viz_h.get_summary_stats()
    stats_v = viz_v.get_summary_stats()

    print("\n" + "="*70)
    print("VISUALIZATION & PHYSICS COMPARISON")
    print("="*70)
    print(f"\nHORIZONTAL BEAM:")
    print(f"  - Axes: X=Position, Y=Deflection (perpendicular to gravity)")
    print(f"  - Self-weight: NOT included in lateral load (acts along axis)")
    print(f"  - Max deflection: {stats_h['max_deflection']*1000:.3f} mm")
    print(f"  - Max stress: {stats_h['max_bending_stress']/1e6:.2f} MPa")

    print(f"\nVERTICAL BEAM:")
    print(f"  - Axes: X=Deflection, Y=Height (along gravity)")
    print(f"  - Self-weight: {problem_v.self_weight_load/1000:.2f} kN/m ADDED to lateral load")
    print(f"  - Total lateral: {problem_v.total_lateral_load/1000:.2f} kN/m")
    print(f"  - Max deflection: {stats_v['max_deflection']*1000:.3f} mm")
    print(f"  - Max stress: {stats_v['max_bending_stress']/1e6:.2f} MPa")

    deflection_increase = ((stats_v['max_deflection'] - stats_h['max_deflection'])
                           / stats_h['max_deflection'] * 100)
    stress_increase = ((stats_v['max_bending_stress'] - stats_h['max_bending_stress'])
                       / stats_h['max_bending_stress'] * 100)

    print(f"\nDIFFERENCE (Vertical vs Horizontal):")
    print(f"  - Deflection increase: +{deflection_increase:.1f}%")
    print(f"  - Stress increase: +{stress_increase:.1f}%")
    print("="*70 + "\n")


if __name__ == '__main__':
    print("\n🏗️  BEAM ORIENTATION VISUALIZATION DEMO\n")
    create_side_by_side_visualization()
