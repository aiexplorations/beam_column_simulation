"""
Demo showing directional point loads (upward and downward).
Tests both positive (downward) and negative (upward) lateral loads on same beam.
"""

import numpy as np
import matplotlib.pyplot as plt
from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver, PointLoad
from visualizer import BeamVisualizer
import materials


def solve_directional_case(title: str, description: str, point_loads: list) -> dict:
    """Solve beam problem with specified directional point loads."""

    section = BeamSection(width=0.06, height=0.15)

    problem = BeamColumnProblem(
        length=2.0,
        section=section,
        material=materials.STEEL,
        axial_load=20000,  # 20 kN axial compression
        lateral_load=3000,  # 3 kN/m lateral load (downward)
        point_loads=point_loads,
        orientation="horizontal",
        include_self_weight=False,
        end_condition="cantilever"
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
        print(f"  ✓ Max shear: {stats['max_shear']/1000:.2f} kN")

        return {
            'x': x, 'v': v, 'M': M, 'V': V,
            'stress': b_stress,
            'stats': stats,
            'problem': problem,
            'title': title,
            'description': description
        }
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("\n" + "="*80)
    print("DIRECTIONAL POINT LOADS DEMONSTRATION")
    print("="*80)
    print("\nBase loading: 3 kN/m distributed lateral load (downward)")
    print("Cantilever beam configuration")

    # Define test cases with different directional loads
    test_cases = [
        ("Case 1: Downward Load at Mid-span",
         "Single 10 kN downward load at 50%",
         [PointLoad(magnitude=10000, position=0.5, as_fraction=True, direction="downward")]),

        ("Case 2: Upward Load at Mid-span",
         "Single 10 kN upward load at 50%",
         [PointLoad(magnitude=10000, position=0.5, as_fraction=True, direction="upward")]),

        ("Case 3: Mixed Directional Loads",
         "10 kN downward at 25%, 8 kN upward at 75%",
         [
             PointLoad(magnitude=10000, position=0.25, as_fraction=True, direction="downward"),
             PointLoad(magnitude=8000, position=0.75, as_fraction=True, direction="upward")
         ]),

        ("Case 4: Symmetric Opposing Loads",
         "5 kN downward at 33%, 5 kN upward at 67%",
         [
             PointLoad(magnitude=5000, position=0.33, as_fraction=True, direction="downward"),
             PointLoad(magnitude=5000, position=0.67, as_fraction=True, direction="upward")
         ]),

        ("Case 5: Triple Load Configuration",
         "8 kN down at 20%, 6 kN up at 50%, 7 kN down at 80%",
         [
             PointLoad(magnitude=8000, position=0.2, as_fraction=True, direction="downward"),
             PointLoad(magnitude=6000, position=0.5, as_fraction=True, direction="upward"),
             PointLoad(magnitude=7000, position=0.8, as_fraction=True, direction="downward")
         ]),
    ]

    # Solve all cases
    results = {}
    valid_results = []

    for title, description, point_loads in test_cases:
        result = solve_directional_case(title, description, point_loads)
        if result is not None:
            results[title] = result
            valid_results.append((title, description, result))

    if not results:
        print("\n✗ No valid solutions obtained!")
        return

    # Create comprehensive comparison plot
    fig = plt.figure(figsize=(18, 15))
    fig.suptitle("Directional Point Loads Effects\n(3 kN/m UDL + Variable Point Loads, Cantilever)",
                 fontsize=16, fontweight='bold')

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']

    # Plot 1: Deflection profiles
    ax = plt.subplot(3, 2, 1)
    for i, (title, _, r) in enumerate(valid_results):
        short_title = title.split(':')[0]
        ax.plot(r['x'], r['v']*1000, label=short_title, linewidth=2.5, color=colors[i])
    ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    ax.set_xlabel("Position (m)", fontsize=11)
    ax.set_ylabel("Deflection (mm)", fontsize=11)
    ax.set_title("Deflection Profiles", fontweight='bold', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Plot 2: Moment diagrams
    ax = plt.subplot(3, 2, 2)
    for i, (title, _, r) in enumerate(valid_results):
        short_title = title.split(':')[0]
        ax.plot(r['x'], r['M']/1000, label=short_title, linewidth=2.5, color=colors[i])
    ax.axhline(y=0, color='k', linewidth=1)
    ax.set_xlabel("Position (m)", fontsize=11)
    ax.set_ylabel("Bending Moment (kN·m)", fontsize=11)
    ax.set_title("Moment Diagrams", fontweight='bold', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 3: Shear force diagrams
    ax = plt.subplot(3, 2, 3)
    for i, (title, _, r) in enumerate(valid_results):
        short_title = title.split(':')[0]
        ax.plot(r['x'], r['V']/1000, label=short_title, linewidth=2.5, color=colors[i])
    ax.axhline(y=0, color='k', linewidth=1)
    ax.set_xlabel("Position (m)", fontsize=11)
    ax.set_ylabel("Shear Force (kN)", fontsize=11)
    ax.set_title("Shear Force Diagrams", fontweight='bold', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 4: Stress distributions
    ax = plt.subplot(3, 2, 4)
    for i, (title, _, r) in enumerate(valid_results):
        short_title = title.split(':')[0]
        ax.plot(r['x'], r['stress']/1e6, label=short_title, linewidth=2.5, color=colors[i])
    ax.set_xlabel("Position (m)", fontsize=11)
    ax.set_ylabel("Bending Stress (MPa)", fontsize=11)
    ax.set_title("Stress Distributions", fontweight='bold', fontsize=12)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Plot 5: Max deflections comparison
    ax = plt.subplot(3, 2, 5)
    case_names = [f"Case {i+1}" for i in range(len(valid_results))]
    max_deflections = [r[2]['stats']['max_deflection']*1000 for r in valid_results]
    bars = ax.bar(case_names, max_deflections, color=colors[:len(valid_results)],
                   alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_ylabel("Max Deflection (mm)", fontsize=11)
    ax.set_title("Maximum Deflections", fontweight='bold', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Plot 6: Max stress comparison
    ax = plt.subplot(3, 2, 6)
    max_stresses = [r[2]['stats']['max_bending_stress']/1e6 for r in valid_results]
    bars = ax.bar(case_names, max_stresses, color=colors[:len(valid_results)],
                   alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_ylabel("Max Stress (MPa)", fontsize=11)
    ax.set_title("Maximum Stresses", fontweight='bold', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('directional_loads_test.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved: directional_loads_test.png")

    # Print detailed comparison table
    print("\n" + "="*80)
    print("DETAILED RESULTS COMPARISON")
    print("="*80)
    print(f"\n{'Case':<25} {'Max Defl (mm)':<20} {'Max Moment (kN·m)':<20} {'Max Stress (MPa)':<20}")
    print("-" * 85)

    for i, (title, _, r) in enumerate(valid_results):
        case_name = f"Case {i+1}"
        defl = r['stats']['max_deflection']*1000
        moment = r['stats']['max_moment']/1000
        stress = r['stats']['max_bending_stress']/1e6
        print(f"{case_name:<25} {defl:>15.3f}      {moment:>15.2f}      {stress:>15.2f}")

    # Analysis and insights
    print("\n" + "="*80)
    print("ANALYSIS: DIRECTIONAL LOAD EFFECTS")
    print("="*80)

    if valid_results:
        max_defl_vals = [(r['stats']['max_deflection']*1000, f"Case {i+1}")
                        for i, (_, _, r) in enumerate(valid_results)]
        max_defl_vals.sort(reverse=True)

        print("\n1. DEFLECTION BEHAVIOR:")
        for i, (defl, case_name) in enumerate(max_defl_vals, 1):
            print(f"   {i}. {case_name:<20} {defl:>8.3f} mm")

        print("\n2. LOAD DIRECTION EFFECTS:")
        print("   - Downward loads: Create positive bending (compression on top)")
        print("   - Upward loads: Create negative bending (tension on top)")
        print("   - Mixed loads: Can cancel or amplify depending on position and magnitude")

        print("\n3. STRESS DISTRIBUTION:")
        upward_result = valid_results[1][2]  # Case 2: Upward load
        downward_result = valid_results[0][2]  # Case 1: Downward load
        upward_stress = upward_result['stats']['max_bending_stress']/1e6
        downward_stress = downward_result['stats']['max_bending_stress']/1e6

        print(f"   - Downward 10 kN at mid-span: {downward_stress:.2f} MPa")
        print(f"   - Upward 10 kN at mid-span: {upward_stress:.2f} MPa")
        if upward_stress > downward_stress:
            ratio = upward_stress / downward_stress
            print(f"   - Upward load is {ratio:.2f}x stiffer in opposing distributed load")
        else:
            ratio = downward_stress / upward_stress
            print(f"   - Downward load is {ratio:.2f}x more severe with distributed load")

        print("\n4. SYMMETRIC VS ASYMMETRIC LOADS:")
        symmetric = valid_results[3][2]  # Case 4
        mixed = valid_results[2][2]  # Case 3
        print(f"   - Symmetric opposing loads (Case 4): {symmetric['stats']['max_deflection']*1000:.3f} mm")
        print(f"   - Non-symmetric loads (Case 3): {mixed['stats']['max_deflection']*1000:.3f} mm")

        print("\n5. DESIGN IMPLICATIONS:")
        print("   - Upward loads reduce deflection from distributed downward loads")
        print("   - Balanced load systems can significantly reduce structural response")
        print("   - Counterweights or uplift loads are effective for deflection control")
        print("   - Direction matters: same magnitude opposite direction ≠ zero effect")

    print("="*80 + "\n")


if __name__ == '__main__':
    main()
