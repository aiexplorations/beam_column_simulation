"""
Demo script showing vertical vs horizontal beam analysis with self-weight.
"""

import numpy as np
import matplotlib.pyplot as plt
from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver
from visualizer import BeamVisualizer
import materials


def analyze_beam(orientation: str, include_weight: bool) -> dict:
    """Analyze a beam with given orientation and weight settings."""

    # Create a steel I-beam-like section
    section = BeamSection(width=0.05, height=0.2)  # 5cm wide, 20cm tall

    problem = BeamColumnProblem(
        length=3.0,  # 3 meter beam
        section=section,
        material=materials.STEEL,
        axial_load=0.0,  # No axial load for this demo
        lateral_load=5000.0,  # 5 kN/m applied load
        point_load=0.0,
        orientation=orientation,
        include_self_weight=include_weight
    )

    # Show self-weight calculation
    self_weight = problem.self_weight_load if include_weight else 0.0
    print(f"\n{'='*60}")
    print(f"Configuration: {orientation.upper()} beam, self-weight={include_weight}")
    print(f"{'='*60}")
    print(f"Section: {section.width*100:.1f}cm × {section.height*100:.1f}cm")
    print(f"Area: {section.area*1e4:.0f} cm²")
    print(f"Material: Steel (density={materials.STEEL.density:.0f} kg/m³)")
    print(f"Beam length: {problem.length:.1f} m")
    print(f"Applied lateral load: {problem.lateral_load/1000:.1f} kN/m")

    if orientation == "vertical" and include_weight:
        print(f"Self-weight load: {self_weight/1000:.2f} kN/m")
        print(f"Total lateral load: {problem.total_lateral_load/1000:.2f} kN/m (includes self-weight)")

    # Solve
    print("Solving...")
    solver = BeamColumnSolver(problem)
    x, v, M, V = solver.solve(num_points=100)
    bending_stress, axial_stress, combined_stress = solver.calculate_stresses(x, M)
    bending_strain, axial_strain = solver.calculate_strains(bending_stress, axial_stress)

    visualizer = BeamVisualizer(
        problem, x, v, M, V,
        bending_stress, axial_stress,
        bending_strain, axial_strain
    )

    stats = visualizer.get_summary_stats()

    print("\nResults:")
    print(f"  Max deflection: {stats['max_deflection']*1000:.3f} mm")
    print(f"  Max bending stress: {stats['max_bending_stress']/1e6:.2f} MPa")
    print(f"  Max moment: {stats['max_moment']/1000:.2f} kN·m")
    print(f"  Max shear force: {stats['max_shear']/1000:.2f} kN")

    return {
        'x': x, 'v': v, 'M': M, 'V': V,
        'stats': stats,
        'problem': problem,
        'visualizer': visualizer
    }


def main():
    print("\n" + "🏗️  BEAM ORIENTATION & SELF-WEIGHT DEMO".center(60))

    # Case 1: Horizontal beam (no self-weight effect)
    h_no_weight = analyze_beam("horizontal", False)

    # Case 2: Horizontal beam (with self-weight, but doesn't affect lateral loading)
    h_with_weight = analyze_beam("horizontal", True)

    # Case 3: Vertical beam (without self-weight)
    v_no_weight = analyze_beam("vertical", False)

    # Case 4: Vertical beam (WITH self-weight - stacks with applied load!)
    v_with_weight = analyze_beam("vertical", True)

    # Create comparison plots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Effect of Beam Orientation and Self-Weight on Deflection", fontsize=14, fontweight='bold')

    # Plot deflections
    ax = axes[0, 0]
    ax.plot(h_no_weight['x'], h_no_weight['v']*1000, 'b-', linewidth=2, label='Horizontal, no weight')
    ax.plot(v_no_weight['x'], v_no_weight['v']*1000, 'r-', linewidth=2, label='Vertical, no weight')
    ax.plot(v_with_weight['x'], v_with_weight['v']*1000, 'g--', linewidth=2.5, label='Vertical, WITH weight')
    ax.set_xlabel('Position (m)')
    ax.set_ylabel('Deflection (mm)')
    ax.set_title('Deflection Profiles')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot moments
    ax = axes[0, 1]
    ax.plot(h_no_weight['x'], h_no_weight['M']/1000, 'b-', linewidth=2, label='Horizontal, no weight')
    ax.plot(v_no_weight['x'], v_no_weight['M']/1000, 'r-', linewidth=2, label='Vertical, no weight')
    ax.plot(v_with_weight['x'], v_with_weight['M']/1000, 'g--', linewidth=2.5, label='Vertical, WITH weight')
    ax.set_xlabel('Position (m)')
    ax.set_ylabel('Bending Moment (kN·m)')
    ax.set_title('Bending Moment Diagrams')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot stresses
    ax = axes[1, 0]
    ax.plot(h_no_weight['x'], h_no_weight['visualizer'].bending_stress/1e6, 'b-', linewidth=2, label='Horizontal, no weight')
    ax.plot(v_no_weight['x'], v_no_weight['visualizer'].bending_stress/1e6, 'r-', linewidth=2, label='Vertical, no weight')
    ax.plot(v_with_weight['x'], v_with_weight['visualizer'].bending_stress/1e6, 'g--', linewidth=2.5, label='Vertical, WITH weight')
    ax.set_xlabel('Position (m)')
    ax.set_ylabel('Bending Stress (MPa)')
    ax.set_title('Stress Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Summary table
    ax = axes[1, 1]
    ax.axis('off')

    summary_data = [
        ['Configuration', 'Max Defl (mm)', 'Max Stress (MPa)', 'Max Moment (kN·m)'],
        ['Horiz, no weight', f"{h_no_weight['stats']['max_deflection']*1000:.2f}",
         f"{h_no_weight['stats']['max_bending_stress']/1e6:.1f}",
         f"{h_no_weight['stats']['max_moment']/1000:.2f}"],
        ['Vert, no weight', f"{v_no_weight['stats']['max_deflection']*1000:.2f}",
         f"{v_no_weight['stats']['max_bending_stress']/1e6:.1f}",
         f"{v_no_weight['stats']['max_moment']/1000:.2f}"],
        ['Vert, WITH weight ⚠️', f"{v_with_weight['stats']['max_deflection']*1000:.2f}",
         f"{v_with_weight['stats']['max_bending_stress']/1e6:.1f}",
         f"{v_with_weight['stats']['max_moment']/1000:.2f}"],
    ]

    # Calculate percentage increase
    weight_increase = ((v_with_weight['stats']['max_deflection'] - v_no_weight['stats']['max_deflection'])
                       / v_no_weight['stats']['max_deflection'] * 100)

    table = ax.table(cellText=summary_data, cellLoc='center', loc='center',
                     colWidths=[0.25, 0.25, 0.25, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Highlight the WITH weight row
    for i in range(4):
        table[(3, i)].set_facecolor('#FFE0B2')

    ax.text(0.5, 0.05, f"⚠️ Self-weight increases deflection by {weight_increase:.1f}% in vertical orientation",
            ha='center', transform=ax.transAxes, fontsize=10, fontweight='bold', color='red')

    plt.tight_layout()
    plt.savefig('demo_orientation_comparison.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved comparison plot: demo_orientation_comparison.png")

    print("\n" + "="*60)
    print("KEY FINDINGS:")
    print("="*60)
    print(f"✓ Horizontal orientation: Self-weight doesn't affect lateral loads")
    print(f"✓ Vertical orientation: Self-weight STACKS with applied loads")
    print(f"✓ Self-weight impact: +{weight_increase:.1f}% deflection increase")
    print(f"✓ Steel section ({0.05*100:.0f}cm × {0.2*100:.0f}cm) self-weight: {v_with_weight['problem'].self_weight_load/1000:.2f} kN/m")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
