"""
Comprehensive test of all boundary conditions including mixed conditions.
Tests: Fixed-Free (Cantilever), Simply Supported, Fixed-Fixed, Hinged-Free,
Fixed-Hinged, and Hinged-Fixed.
"""

import numpy as np
import matplotlib.pyplot as plt
from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver, PointLoad
from visualizer import BeamVisualizer
import materials


def solve_boundary_condition(end_condition: str, title: str, description: str) -> dict:
    """Solve beam problem for given boundary condition."""

    section = BeamSection(width=0.06, height=0.15)

    problem = BeamColumnProblem(
        length=2.0,
        section=section,
        material=materials.STEEL,
        axial_load=20000,  # 20 kN axial compression
        lateral_load=6000,  # 6 kN/m lateral load
        point_loads=[PointLoad(magnitude=5000, position=0.5, as_fraction=True)],  # 5 kN at mid-span
        orientation="horizontal",
        include_self_weight=False,
        end_condition=end_condition
    )

    print(f"\nSolving: {title}")
    print(f"  {description}")

    try:
        solver = BeamColumnSolver(problem)
        x, v, M, V = solver.solve(num_points=100)
        b_stress, a_stress, _ = solver.calculate_stresses(x, M)
        b_strain, a_strain = solver.calculate_strains(b_stress, a_stress)

        visualizer = BeamVisualizer(problem, x, v, M, V, b_stress, a_stress, b_strain, a_strain)
        stats = visualizer.get_summary_stats()

        print(f"  ✓ Max deflection: {stats['max_deflection']*1000:.3f} mm")
        print(f"  ✓ Max stress: {stats['max_bending_stress']/1e6:.2f} MPa")
        print(f"  ✓ Max moment: {stats['max_moment']/1000:.2f} kN·m")

        return {
            'x': x, 'v': v, 'M': M, 'V': V,
            'stress': b_stress,
            'stats': stats,
            'problem': problem,
            'title': title,
            'condition': end_condition
        }
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return None


def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE BOUNDARY CONDITIONS TEST")
    print("="*80)
    print("\nTesting all 6 boundary conditions with identical loading:")
    print("  - Axial load: 20 kN (compression)")
    print("  - Distributed lateral load: 6 kN/m")
    print("  - Point load: 5 kN at mid-span (50%)")

    # Define all boundary conditions
    boundary_conditions = [
        ("cantilever",
         "Cantilever (Fixed-Free)",
         "One end fixed, other end free"),
        ("simply_supported",
         "Simply Supported (Hinged-Hinged)",
         "Both ends hinged (can rotate, cannot translate)"),
        ("fixed_fixed",
         "Fixed-Fixed (Both Fixed)",
         "Both ends fixed (cannot rotate or translate)"),
        ("hinged_free",
         "Hinged-Free (Pinned-Free)",
         "One end hinged, other end free"),
        ("fixed_hinged",
         "Fixed-Hinged (Fixed-Hinged)",
         "One end fixed, other end hinged - MIXED"),
        ("hinged_fixed",
         "Hinged-Fixed (Hinged-Fixed)",
         "One end hinged, other end fixed - MIXED"),
    ]

    # Solve all boundary conditions
    results = {}
    valid_results = []

    for condition, title, description in boundary_conditions:
        result = solve_boundary_condition(condition, title, description)
        if result is not None:
            results[condition] = result
            valid_results.append((condition, title, result))

    if not results:
        print("\n✗ No valid solutions obtained!")
        return

    # Create comprehensive comparison plot
    fig = plt.figure(figsize=(18, 14))
    fig.suptitle("All Boundary Conditions Comparison\n(20 kN axial + 6 kN/m UDL + 5 kN point load at 50%)",
                 fontsize=16, fontweight='bold')

    conditions = [r[0] for r in valid_results]
    titles = [r[1] for r in valid_results]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']

    # Plot 1: Deflection profiles
    ax = plt.subplot(3, 3, 1)
    for i, (cond, title, r) in enumerate(valid_results):
        ax.plot(r['x'], r['v']*1000, label=title, linewidth=2.5, color=colors[i])
    ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    ax.set_xlabel("Position (m)", fontsize=10)
    ax.set_ylabel("Deflection (mm)", fontsize=10)
    ax.set_title("Deflection Profiles", fontweight='bold', fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # Plot 2: Moment diagrams
    ax = plt.subplot(3, 3, 2)
    for i, (cond, title, r) in enumerate(valid_results):
        ax.plot(r['x'], r['M']/1000, label=title, linewidth=2.5, color=colors[i])
    ax.axhline(y=0, color='k', linewidth=1)
    ax.set_xlabel("Position (m)", fontsize=10)
    ax.set_ylabel("Bending Moment (kN·m)", fontsize=10)
    ax.set_title("Moment Diagrams", fontweight='bold', fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 3: Shear force diagrams
    ax = plt.subplot(3, 3, 3)
    for i, (cond, title, r) in enumerate(valid_results):
        ax.plot(r['x'], r['V']/1000, label=title, linewidth=2.5, color=colors[i])
    ax.axhline(y=0, color='k', linewidth=1)
    ax.set_xlabel("Position (m)", fontsize=10)
    ax.set_ylabel("Shear Force (kN)", fontsize=10)
    ax.set_title("Shear Force Diagrams", fontweight='bold', fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 4: Stress distributions
    ax = plt.subplot(3, 3, 4)
    for i, (cond, title, r) in enumerate(valid_results):
        ax.plot(r['x'], r['stress']/1e6, label=title, linewidth=2.5, color=colors[i])
    ax.set_xlabel("Position (m)", fontsize=10)
    ax.set_ylabel("Bending Stress (MPa)", fontsize=10)
    ax.set_title("Stress Distributions", fontweight='bold', fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # Plot 5: Max deflections comparison
    ax = plt.subplot(3, 3, 5)
    max_deflections = [r['stats']['max_deflection']*1000 for _, _, r in valid_results]
    short_labels = [t.split('(')[0].strip() for _, t, _ in valid_results]
    bars = ax.bar(range(len(valid_results)), max_deflections, color=colors[:len(valid_results)],
                   alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_ylabel("Max Deflection (mm)", fontsize=10)
    ax.set_title("Maximum Deflections", fontweight='bold', fontsize=11)
    ax.set_xticks(range(len(valid_results)))
    ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Plot 6: Max moments comparison
    ax = plt.subplot(3, 3, 6)
    max_moments = [r['stats']['max_moment']/1000 for _, _, r in valid_results]
    bars = ax.bar(range(len(valid_results)), max_moments, color=colors[:len(valid_results)],
                   alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_ylabel("Max Moment (kN·m)", fontsize=10)
    ax.set_title("Maximum Moments", fontweight='bold', fontsize=11)
    ax.set_xticks(range(len(valid_results)))
    ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Plot 7: Max stress comparison
    ax = plt.subplot(3, 3, 7)
    max_stresses = [r['stats']['max_bending_stress']/1e6 for _, _, r in valid_results]
    bars = ax.bar(range(len(valid_results)), max_stresses, color=colors[:len(valid_results)],
                   alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_ylabel("Max Stress (MPa)", fontsize=10)
    ax.set_title("Maximum Stresses", fontweight='bold', fontsize=11)
    ax.set_xticks(range(len(valid_results)))
    ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Plot 8: Stiffness ranking (inverse of deflection)
    ax = plt.subplot(3, 3, 8)
    stiffness_ranking = [1.0 / (d if d > 0 else 0.001) for d in max_deflections]
    normalized_stiffness = [s / max(stiffness_ranking) * 100 for s in stiffness_ranking]
    bars = ax.barh(range(len(valid_results)), normalized_stiffness, color=colors[:len(valid_results)],
                    alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_xlabel("Relative Stiffness (%)", fontsize=10)
    ax.set_title("Stiffness Ranking (100% = Stiffest)", fontweight='bold', fontsize=11)
    ax.set_yticks(range(len(valid_results)))
    ax.set_yticklabels(short_labels, fontsize=8)
    ax.grid(True, alpha=0.3, axis='x')
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2.,
               f'{width:.0f}%', ha='left', va='center', fontsize=8, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Plot 9: Summary table as text
    ax = plt.subplot(3, 3, 9)
    ax.axis('off')

    table_data = [['Boundary Condition', 'Deflection\n(mm)', 'Moment\n(kN·m)', 'Stress\n(MPa)']]
    for _, title, r in valid_results:
        short_title = title.split('(')[0].strip()
        table_data.append([
            short_title,
            f"{r['stats']['max_deflection']*1000:.2f}",
            f"{r['stats']['max_moment']/1000:.1f}",
            f"{r['stats']['max_bending_stress']/1e6:.1f}"
        ])

    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.35, 0.2, 0.2, 0.2])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2)

    # Color header row
    for i in range(4):
        table[(0, i)].set_facecolor('#4ECDC4')
        table[(0, i)].set_text_props(weight='bold', color='white')

    plt.tight_layout()
    plt.savefig('all_boundary_conditions_test.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved: all_boundary_conditions_test.png")

    # Print detailed comparison table
    print("\n" + "="*80)
    print("DETAILED RESULTS COMPARISON")
    print("="*80)
    print(f"\n{'Boundary Condition':<25} {'Max Defl (mm)':<20} {'Max Moment (kN·m)':<20} {'Max Stress (MPa)':<20}")
    print("-" * 85)

    for cond, title, r in valid_results:
        defl = r['stats']['max_deflection']*1000
        moment = r['stats']['max_moment']/1000
        stress = r['stats']['max_bending_stress']/1e6
        short_title = title.split('(')[0].strip()
        print(f"{short_title:<25} {defl:>15.3f}      {moment:>15.2f}      {stress:>15.2f}")

    # Analysis and insights
    print("\n" + "="*80)
    print("ANALYSIS: BOUNDARY CONDITION EFFECTS")
    print("="*80)

    if valid_results:
        max_defl_vals = [(r['stats']['max_deflection']*1000, t.split('(')[0].strip())
                        for _, t, r in valid_results]
        max_defl_vals.sort()

        max_stress_vals = [(r['stats']['max_bending_stress']/1e6, t.split('(')[0].strip())
                          for _, t, r in valid_results]
        max_stress_vals.sort()

        print("\n1. DEFLECTION RANKING (from stiffest to most flexible):")
        for i, (defl, cond) in enumerate(max_defl_vals, 1):
            baseline = max_defl_vals[-1][0]
            percent = (defl / baseline * 100) if baseline > 0 else 0
            print(f"   {i}. {cond:<20} {defl:>8.3f} mm  ({percent:>6.1f}% of most flexible)")

        print("\n2. STRESS RANKING (from highest to lowest):")
        max_stress_vals.sort(reverse=True)
        for i, (stress, cond) in enumerate(max_stress_vals, 1):
            print(f"   {i}. {cond:<20} {stress:>8.2f} MPa")

        print("\n3. KEY OBSERVATIONS:")

        most_stiff = max_defl_vals[0]
        most_flexible = max_defl_vals[-1]
        flexibility_ratio = most_flexible[0] / most_stiff[0] if most_stiff[0] > 0 else 1.0

        print(f"   - Stiffest condition: {most_stiff[1]} ({most_stiff[0]:.3f} mm)")
        print(f"   - Most flexible condition: {most_flexible[1]} ({most_flexible[0]:.3f} mm)")
        print(f"   - Flexibility ratio: {flexibility_ratio:.2f}x")

        print("\n4. STRUCTURAL BEHAVIOR:")
        print("   - Fixed-Fixed: Constrains both ends, provides maximum stiffness")
        print("   - Simply Supported: Allows rotation at both ends, intermediate stiffness")
        print("   - Cantilever: Only one end fixed, flexible")
        print("   - Hinged-Free: Similar to cantilever but with pinned support")
        print("   - Mixed conditions (Fixed-Hinged, Hinged-Fixed): Intermediate behavior")

        print("\n5. DESIGN RECOMMENDATIONS:")
        print("   - Use Fixed-Fixed for maximum stiffness and load capacity")
        print("   - Use Simply Supported for symmetric loading and deflection control")
        print("   - Avoid Hinged-Free configuration (least efficient)")
        print("   - Mixed conditions offer trade-offs between cost and performance")

    print("="*80 + "\n")


if __name__ == '__main__':
    main()
