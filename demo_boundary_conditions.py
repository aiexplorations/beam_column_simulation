"""
Demo showcasing different beam boundary conditions and their effects.
"""

import numpy as np
import matplotlib.pyplot as plt
from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver
from visualizer import BeamVisualizer
import materials


def solve_and_analyze(end_condition: str, title: str) -> dict:
    """Solve beam problem for given boundary condition."""

    section = BeamSection(width=0.06, height=0.15)

    problem = BeamColumnProblem(
        length=2.0,
        section=section,
        material=materials.STEEL,
        axial_load=20000,  # 20 kN axial compression
        lateral_load=6000,  # 6 kN/m lateral load
        point_load=5000,   # 5 kN point load (where applicable)
        orientation="horizontal",
        include_self_weight=False,
        end_condition=end_condition
    )

    print(f"\nSolving: {title}")
    print(f"  Boundary condition: {end_condition}")

    solver = BeamColumnSolver(problem)
    x, v, M, V = solver.solve(num_points=100)
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
        'problem': problem,
        'title': title
    }


def main():
    print("\n" + "="*70)
    print("BOUNDARY CONDITIONS COMPARISON")
    print("="*70)

    # Solve all four boundary conditions
    results = {
        'Cantilever': solve_and_analyze("cantilever", "Cantilever (Fixed-Free)"),
        'Simply Supported': solve_and_analyze("simply_supported", "Simply Supported (Hinged-Hinged)"),
        'Fixed-Fixed': solve_and_analyze("fixed_fixed", "Fixed-Fixed (Both Fixed)"),
        'Hinged-Free': solve_and_analyze("hinged_free", "Hinged-Free (Pinned-Free)")
    }

    # Create comprehensive comparison plot
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle("Beam Boundary Conditions Comparison", fontsize=16, fontweight='bold')

    conditions = ['Cantilever', 'Simply Supported', 'Fixed-Fixed', 'Hinged-Free']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']

    # Plot 1: Deflection profiles
    ax = plt.subplot(2, 3, 1)
    for cond, color in zip(conditions, colors):
        r = results[cond]
        ax.plot(r['x'], r['v']*1000, label=cond, linewidth=2.5, color=color)
    ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    ax.set_xlabel("Position (m)", fontsize=11)
    ax.set_ylabel("Deflection (mm)", fontsize=11)
    ax.set_title("Deflection Profiles", fontweight='bold', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Plot 2: Moment diagrams
    ax = plt.subplot(2, 3, 2)
    for cond, color in zip(conditions, colors):
        r = results[cond]
        ax.plot(r['x'], r['M']/1000, label=cond, linewidth=2.5, color=color)
    ax.axhline(y=0, color='k', linewidth=1)
    ax.set_xlabel("Position (m)", fontsize=11)
    ax.set_ylabel("Bending Moment (kN·m)", fontsize=11)
    ax.set_title("Moment Diagrams", fontweight='bold', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 3: Shear force diagrams
    ax = plt.subplot(2, 3, 3)
    for cond, color in zip(conditions, colors):
        r = results[cond]
        ax.plot(r['x'], r['V']/1000, label=cond, linewidth=2.5, color=color)
    ax.axhline(y=0, color='k', linewidth=1)
    ax.set_xlabel("Position (m)", fontsize=11)
    ax.set_ylabel("Shear Force (kN)", fontsize=11)
    ax.set_title("Shear Force Diagrams", fontweight='bold', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 4: Stress distributions
    ax = plt.subplot(2, 3, 4)
    for cond, color in zip(conditions, colors):
        r = results[cond]
        ax.plot(r['x'], r['stress']/1e6, label=cond, linewidth=2.5, color=color)
    ax.set_xlabel("Position (m)", fontsize=11)
    ax.set_ylabel("Bending Stress (MPa)", fontsize=11)
    ax.set_title("Stress Distributions", fontweight='bold', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Plot 5: Max values comparison (bar chart)
    ax = plt.subplot(2, 3, 5)
    max_deflections = [results[c]['stats']['max_deflection']*1000 for c in conditions]
    bars = ax.bar(conditions, max_deflections, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_ylabel("Max Deflection (mm)", fontsize=11)
    ax.set_title("Maximum Deflections", fontweight='bold', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    # Add values on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Plot 6: Max stress comparison
    ax = plt.subplot(2, 3, 6)
    max_stresses = [results[c]['stats']['max_bending_stress']/1e6 for c in conditions]
    bars = ax.bar(conditions, max_stresses, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_ylabel("Max Stress (MPa)", fontsize=11)
    ax.set_title("Maximum Stresses", fontweight='bold', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    # Add values on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('boundary_conditions_comparison.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved: boundary_conditions_comparison.png")

    # Print detailed comparison table
    print("\n" + "="*70)
    print("DETAILED RESULTS COMPARISON")
    print("="*70)
    print(f"\n{'Boundary Condition':<25} {'Max Defl (mm)':<20} {'Max Stress (MPa)':<20}")
    print("-" * 70)

    for cond in conditions:
        r = results[cond]
        defl = r['stats']['max_deflection']*1000
        stress = r['stats']['max_bending_stress']/1e6
        print(f"{cond:<25} {defl:>15.3f}      {stress:>15.2f}")

    # Key observations
    print("\n" + "="*70)
    print("KEY OBSERVATIONS")
    print("="*70)

    c_defl = results['Cantilever']['stats']['max_deflection']
    ss_defl = results['Simply Supported']['stats']['max_deflection']
    ff_defl = results['Fixed-Fixed']['stats']['max_deflection']
    hf_defl = results['Hinged-Free']['stats']['max_deflection']

    print(f"\n1. DEFLECTION RANKING:")
    print(f"   Cantilever:       {c_defl*1000:.3f} mm (baseline)")
    print(f"   Hinged-Free:      {hf_defl*1000:.3f} mm ({hf_defl/c_defl*100:.1f}% of cantilever)")
    print(f"   Simply Supported: {ss_defl*1000:.3f} mm ({ss_defl/c_defl*100:.1f}% of cantilever)")
    print(f"   Fixed-Fixed:      {ff_defl*1000:.3f} mm ({ff_defl/c_defl*100:.1f}% of cantilever)")

    print(f"\n2. STIFFNESS:")
    print(f"   - Fixed-Fixed is STIFFEST (minimal deflection)")
    print(f"   - Cantilever is MOST FLEXIBLE (maximum deflection)")
    print(f"   - Simply Supported and Hinged-Free are intermediate")

    print(f"\n3. MOMENT DISTRIBUTION:")
    print(f"   - Cantilever: Large moment at support")
    print(f"   - Simply Supported: Moment varies smoothly")
    print(f"   - Fixed-Fixed: High moments at both ends")
    print(f"   - Hinged-Free: Moment only at support")

    print("="*70 + "\n")


if __name__ == '__main__':
    main()
