"""
Demo showing the effect of point load position on beam deflection and stress.
Demonstrates how load location affects internal forces and stresses.
"""

import numpy as np
import matplotlib.pyplot as plt
from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver, PointLoad
from visualizer import BeamVisualizer
import materials


def solve_with_point_load_at(position_fraction: float, position_label: str) -> dict:
    """Solve beam with point load at specified position."""

    section = BeamSection(width=0.08, height=0.16)

    # Create point load at specified position
    point_loads = [PointLoad(magnitude=15000, position=position_fraction, as_fraction=True)]

    problem = BeamColumnProblem(
        length=2.5,
        section=section,
        material=materials.STEEL,
        axial_load=30000,  # 30 kN axial
        lateral_load=4000,  # 4 kN/m distributed
        point_loads=point_loads,
        orientation="horizontal",
        include_self_weight=False,
        end_condition="cantilever"
    )

    print(f"\nSolving: Point load at {position_label}")
    print(f"  Position: {position_fraction*100:.0f}% along beam")

    solver = BeamColumnSolver(problem)
    x, v, M, V = solver.solve(num_points=150)
    b_stress, a_stress, _ = solver.calculate_stresses(x, M)
    b_strain, a_strain = solver.calculate_strains(b_stress, a_stress)

    visualizer = BeamVisualizer(problem, x, v, M, V, b_stress, a_stress, b_strain, a_strain)
    stats = visualizer.get_summary_stats()

    print(f"  Max deflection: {stats['max_deflection']*1000:.3f} mm")
    print(f"  Max stress: {stats['max_bending_stress']/1e6:.2f} MPa")
    print(f"  Max moment: {stats['max_moment']/1000:.2f} kN·m")

    return {
        'x': x, 'v': v, 'M': M, 'V': V,
        'stress': b_stress,
        'stats': stats,
        'position': position_fraction,
        'label': position_label,
        'problem': problem
    }


def main():
    print("\n" + "="*70)
    print("POINT LOAD POSITION EFFECTS")
    print("="*70)

    # Solve for different point load positions
    positions = {
        'Free End (x=0)': solve_with_point_load_at(0.0, "Free End"),
        '25% (0.625m)': solve_with_point_load_at(0.25, "1/4 Length"),
        '50% Mid-span (1.25m)': solve_with_point_load_at(0.50, "Mid-span"),
        '75% (1.875m)': solve_with_point_load_at(0.75, "3/4 Length"),
        'Support (x=L)': solve_with_point_load_at(1.0, "Fixed Support")
    }

    # Create comprehensive comparison plot
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle("Effect of Point Load Position on Beam Response\n(15 kN point load + 4 kN/m UDL, 30 kN axial)",
                 fontsize=14, fontweight='bold')

    # Shared x-axis (position)
    x_ref = list(positions.values())[0]['x']
    colors_pos = ['#FF6B6B', '#FFA07A', '#FFD700', '#90EE90', '#6495ED']

    # Plot 1: Deflection for different load positions
    ax = plt.subplot(2, 3, 1)
    for (label, color) in zip(positions.keys(), colors_pos):
        r = positions[label]
        ax.plot(r['x'], r['v']*1000, label=label, linewidth=2.5, color=color)
    ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    ax.set_xlabel("Position (m)", fontsize=10)
    ax.set_ylabel("Deflection (mm)", fontsize=10)
    ax.set_title("Deflection Profiles", fontweight='bold', fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # Plot 2: Moment diagrams
    ax = plt.subplot(2, 3, 2)
    for (label, color) in zip(positions.keys(), colors_pos):
        r = positions[label]
        ax.plot(r['x'], r['M']/1000, label=label, linewidth=2.5, color=color)
    ax.axhline(y=0, color='k', linewidth=1)
    ax.set_xlabel("Position (m)", fontsize=10)
    ax.set_ylabel("Moment (kN·m)", fontsize=10)
    ax.set_title("Bending Moment Diagrams", fontweight='bold', fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 3: Shear force diagrams
    ax = plt.subplot(2, 3, 3)
    for (label, color) in zip(positions.keys(), colors_pos):
        r = positions[label]
        ax.plot(r['x'], r['V']/1000, label=label, linewidth=2.5, color=color)
    ax.axhline(y=0, color='k', linewidth=1)
    ax.set_xlabel("Position (m)", fontsize=10)
    ax.set_ylabel("Shear Force (kN)", fontsize=10)
    ax.set_title("Shear Force Diagrams", fontweight='bold', fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 4: Stress distributions
    ax = plt.subplot(2, 3, 4)
    for (label, color) in zip(positions.keys(), colors_pos):
        r = positions[label]
        ax.plot(r['x'], r['stress']/1e6, label=label, linewidth=2.5, color=color)
    ax.set_xlabel("Position (m)", fontsize=10)
    ax.set_ylabel("Bending Stress (MPa)", fontsize=10)
    ax.set_title("Stress Distributions", fontweight='bold', fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # Plot 5: Max metrics vs load position
    ax = plt.subplot(2, 3, 5)
    pos_pct = [pos_data['position']*100 for pos_data in positions.values()]
    max_deflections = [r['stats']['max_deflection']*1000 for r in positions.values()]
    ax.plot(pos_pct, max_deflections, 'o-', linewidth=3, markersize=10, color='#FF6B6B')
    ax.set_xlabel("Load Position (% from free end)", fontsize=10)
    ax.set_ylabel("Max Deflection (mm)", fontsize=10)
    ax.set_title("Max Deflection vs Load Position", fontweight='bold', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-5, 105)

    # Plot 6: Max moment vs load position
    ax = plt.subplot(2, 3, 6)
    max_moments = [r['stats']['max_moment']/1000 for r in positions.values()]
    ax.plot(pos_pct, max_moments, 's-', linewidth=3, markersize=10, color='#4ECDC4')
    ax.set_xlabel("Load Position (% from free end)", fontsize=10)
    ax.set_ylabel("Max Moment (kN·m)", fontsize=10)
    ax.set_title("Max Moment vs Load Position", fontweight='bold', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-5, 105)

    plt.tight_layout()
    plt.savefig('point_load_position_effects.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved: point_load_position_effects.png")

    # Print analysis
    print("\n" + "="*70)
    print("ANALYSIS: POINT LOAD POSITION EFFECTS")
    print("="*70)
    print(f"\n{'Position':<25} {'Max Defl (mm)':<18} {'Max Stress (MPa)':<18}")
    print("-" * 70)

    for label, r in positions.items():
        defl = r['stats']['max_deflection']*1000
        stress = r['stats']['max_bending_stress']/1e6
        print(f"{label:<25} {defl:>15.3f}      {stress:>15.2f}")

    # Key observations
    print("\n" + "="*70)
    print("KEY INSIGHTS")
    print("="*70)

    max_defl_free = positions['Free End (x=0)']['stats']['max_deflection']*1000
    max_defl_mid = positions['50% Mid-span (1.25m)']['stats']['max_deflection']*1000
    max_defl_fixed = positions['Support (x=L)']['stats']['max_deflection']*1000

    print(f"\n1. DEFLECTION:")
    print(f"   - Load at FREE END: {max_defl_free:.3f} mm (maximum)")
    print(f"   - Load at MID-SPAN: {max_defl_mid:.3f} mm ({max_defl_mid/max_defl_free*100:.1f}% of free end)")
    print(f"   - Load at SUPPORT:  {max_defl_fixed:.3f} mm (minimum)")

    print(f"\n2. PATTERN:")
    print(f"   - Moving load CLOSER to fixed support REDUCES deflection")
    print(f"   - Load position is CRITICAL to structural behavior")
    print(f"   - Free end load is ~{max_defl_free/max_defl_fixed:.1f}x worse than support location")

    print(f"\n3. DESIGN IMPLICATIONS:")
    print(f"   - Place heavy loads as CLOSE to support as possible")
    print(f"   - Cantilever beams are MOST SENSITIVE to free end loads")
    print(f"   - Mid-span loading is intermediate in severity")

    print("="*70 + "\n")


if __name__ == '__main__':
    main()
