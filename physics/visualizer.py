"""
Visualization system for beam-column analysis with FEA-style heat maps.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.patches as patches
from typing import Tuple


class BeamVisualizer:
    """Creates FEA-style visualizations of beam-column analysis results."""

    def __init__(self, problem, x: np.ndarray, v: np.ndarray, M: np.ndarray, V: np.ndarray,
                 bending_stress: np.ndarray, axial_stress: np.ndarray,
                 bending_strain: np.ndarray, axial_strain: np.ndarray):
        """
        Initialize visualizer with analysis results.

        Args:
            problem: BeamColumnProblem instance
            x: Position along beam
            v: Lateral deflections
            M: Bending moments
            V: Shear forces
            bending_stress: Bending stresses
            axial_stress: Axial stresses
            bending_strain: Bending strains
            axial_strain: Axial strains
        """
        self.problem = problem
        self.x = x
        self.v = v
        self.M = M
        self.V = V
        self.bending_stress = bending_stress
        self.axial_stress = axial_stress
        self.bending_strain = bending_strain
        self.axial_strain = axial_strain

    def create_comprehensive_plot(self) -> plt.Figure:
        """
        Create a comprehensive visualization with 4 subplots:
        1. Deflected shape with stress heat map
        2. Bending stress distribution
        3. Axial stress distribution
        4. Strain distribution

        Solves the coupled ODE system:
        - d²v/dx² = M/(EI) (curvature relation)
        - dM/dx = V (moment equilibrium)
        - dV/dx = -q (shear equilibrium)
        - P-Δ effect from axial load coupling
        """
        orientation_label = "Vertical" if self.problem.orientation == "vertical" else "Horizontal"
        fig = plt.figure(figsize=(16, 12), dpi=300)
        fig.suptitle(f"Beam-Column ODE Analysis: Numerical Solution of Timoshenko-Beam Equations\n({orientation_label} Beam with P-Δ Coupling)",
                     fontsize=16, fontweight='bold', y=0.995)

        # Subplot 1: Deflected shape with bending stress heat map
        ax1 = plt.subplot(2, 3, 1)
        self._plot_deflected_beam_with_stress(ax1, self.bending_stress, "σ_b(x) - Bending Stress")

        # Subplot 2: Bending stress distribution (σ = M*c/I from Euler-Bernoulli)
        ax2 = plt.subplot(2, 3, 2)
        self._plot_stress_heatmap(ax2, self.bending_stress, "Bending Stress σ_b = M(x)·c/I")

        # Subplot 3: Axial stress distribution (σ_a = P/A)
        ax3 = plt.subplot(2, 3, 3)
        self._plot_stress_heatmap(ax3, self.axial_stress, "Axial Stress σ_a = P/A")

        # Subplot 4: Combined stress from ODE solution
        ax4 = plt.subplot(2, 3, 4)
        combined_stress = np.sqrt(self.bending_stress**2 + self.axial_stress**2)
        self._plot_stress_heatmap(ax4, combined_stress, "Combined Stress σ = √(σ_b² + σ_a²)")

        # Subplot 5: Lateral deflection v(x) from ODE solution
        ax5 = plt.subplot(2, 3, 5)
        self._plot_deflection(ax5)

        # Subplot 6: Bending moment M(x) from ODE integration
        ax6 = plt.subplot(2, 3, 6)
        self._plot_moment_diagram(ax6)

        plt.tight_layout(rect=[0, 0, 1, 0.98])
        return fig

    def _plot_deflected_beam_with_stress(self, ax, stress: np.ndarray, title: str):
        """Plot deflected beam shape with stress color coding, showing orientation."""
        # Normalize stress for color mapping
        norm = Normalize(vmin=np.min(stress), vmax=np.max(stress))
        cmap = plt.cm.RdYlBu_r  # Red for high stress, blue for low

        # Determine orientation and adjust plot accordingly
        is_vertical = self.problem.orientation == "vertical"

        if is_vertical:
            # Vertical beam: x-axis is vertical (gravity acts downward)
            # Plot beam with gravity indication
            for i in range(len(self.x) - 1):
                stress_val = (stress[i] + stress[i + 1]) / 2
                color = cmap(norm(stress_val))
                # Swap axes for vertical: position is y-axis, deflection is x-axis
                ax.plot(self.v[i:i + 2], self.x[i:i + 2], linewidth=3, color=color)

            # Add original position (vertical line)
            ax.plot(np.zeros_like(self.x), self.x, 'k--', linewidth=1, alpha=0.3, label='Original')

            # Draw fixed support at top
            h = self.problem.section.height
            rect = patches.Rectangle((-h / 2, self.x[-1] - 0.01), h, 0.01,
                                     edgecolor='black', facecolor='gray', alpha=0.5)
            ax.add_patch(rect)

            # Add gravity arrow
            ax.arrow(self.x[-1] * 0.8, 0.1, 0, -0.3, head_width=0.002, head_length=0.05,
                    fc='red', ec='red', linewidth=2, alpha=0.7)
            ax.text(self.x[-1] * 0.8 + 0.01, 0.05, 'g', fontsize=12, color='red', fontweight='bold')

            ax.set_xlabel("Deflection (m)", fontsize=11)
            ax.set_ylabel("Height (m)", fontsize=11)
            ax.set_title("Vertical Beam - Deflected Shape (gravity acts downward)", fontsize=12, fontweight='bold')

        else:
            # Horizontal beam: standard plot
            for i in range(len(self.x) - 1):
                stress_val = (stress[i] + stress[i + 1]) / 2
                color = cmap(norm(stress_val))
                ax.plot(self.x[i:i + 2], self.v[i:i + 2], linewidth=3, color=color)

            # Add original position
            ax.plot(self.x, np.zeros_like(self.x), 'k--', linewidth=1, alpha=0.3, label='Original')

            # Draw section at fixed end
            h = self.problem.section.height
            w = self.problem.section.width
            rect = patches.Rectangle((self.x[-1] - 0.01, -h / 2), 0.01, h,
                                     edgecolor='black', facecolor='gray', alpha=0.5)
            ax.add_patch(rect)

            ax.set_xlabel("Position (m)", fontsize=11)
            ax.set_ylabel("Deflection (m)", fontsize=11)
            ax.set_title("Horizontal Beam - Deflected Shape", fontsize=12, fontweight='bold')

        # Colorbar
        sm = ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label(f"{title} (Pa)", fontsize=10)

        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_stress_heatmap(self, ax, stress: np.ndarray, title: str):
        """Create a 2D heat map visualization of stress across the beam cross-section."""
        # Create a 2D array showing stress variation across beam height
        n_height = 20
        height_positions = np.linspace(-self.problem.section.height / 2,
                                       self.problem.section.height / 2, n_height)

        # For each position along beam, stress varies linearly across height
        stress_2d = np.zeros((n_height, len(self.x)))
        for i, s in enumerate(stress):
            # Stress varies linearly from -s to +s across height
            stress_2d[:, i] = s * (height_positions / (self.problem.section.height / 2))

        # Plot heat map
        im = ax.contourf(self.x, height_positions, stress_2d, levels=20, cmap='RdYlBu_r')
        ax.contour(self.x, height_positions, stress_2d, levels=5, colors='black', alpha=0.2, linewidths=0.5)

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Stress (Pa)", fontsize=10)

        ax.set_xlabel("Position along Beam (m)", fontsize=11)
        ax.set_ylabel("Distance from Neutral Axis (m)", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')

    def _plot_deflection(self, ax):
        """Plot lateral deflection profile v(x) from ODE solution."""
        ax.fill_between(self.x, self.v, alpha=0.3, color='blue')
        ax.plot(self.x, self.v, 'b-', linewidth=2.5, label='v(x)')
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, label='Original axis')
        ax.set_xlabel("Position x (m)", fontsize=11)
        ax.set_ylabel("Lateral Deflection v(x) (m)", fontsize=11)
        ax.set_title("Lateral Deflection: v(x) from dv/dx solution", fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10)

    def _plot_moment_diagram(self, ax):
        """Plot bending moment diagram M(x) from ODE integration."""
        colors = np.where(self.M >= 0, 'blue', 'red')
        ax.bar(self.x, self.M, width=self.x[1] - self.x[0], color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
        ax.axhline(y=0, color='k', linewidth=1.5)
        ax.set_xlabel("Position x (m)", fontsize=11)
        ax.set_ylabel("Bending Moment M(x) (N·m)", fontsize=11)
        ax.set_title("Bending Moment: M(x) from dM/dx = V integration", fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

    def create_simple_plot(self) -> plt.Figure:
        """Create a simpler 2x2 visualization for quick analysis of ODE solution."""
        is_vertical = self.problem.orientation == "vertical"
        orientation_label = "Vertical" if is_vertical else "Horizontal"

        fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
        fig.suptitle(f"Beam-Column ODE Solution: Quick Analysis ({orientation_label} Beam)\nNumerical Integration of Coupled Differential Equations",
                     fontsize=15, fontweight='bold', y=0.995)

        # Deflection with stress overlay
        ax = axes[0, 0]
        norm = Normalize(vmin=0, vmax=np.max(self.bending_stress))
        cmap = plt.cm.hot

        if is_vertical:
            # Vertical orientation
            scatter = ax.scatter(self.v, self.x, c=self.bending_stress, cmap=cmap, s=50)
            ax.plot(self.v, self.x, 'k-', linewidth=1, alpha=0.5)
            ax.set_xlabel("Deflection (m)", fontsize=11)
            ax.set_ylabel("Height (m)", fontsize=11)
            ax.axvline(x=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
            # Add gravity indicator
            ax.arrow(np.min(self.v) + 0.001, self.x[-1] * 0.9, 0, -0.2,
                    head_width=0.003, head_length=0.05, fc='red', ec='red', alpha=0.7)
            ax.text(np.min(self.v) + 0.003, self.x[-1] * 0.85, 'g', fontsize=11, color='red', fontweight='bold')
        else:
            # Horizontal orientation
            scatter = ax.scatter(self.x, self.v, c=self.bending_stress, cmap=cmap, s=50)
            ax.plot(self.x, self.v, 'k-', linewidth=1, alpha=0.5)
            ax.set_xlabel("Position (m)", fontsize=11)
            ax.set_ylabel("Deflection (m)", fontsize=11)
            ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.3)

        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Stress (Pa)", fontsize=10)
        ax.set_title("Deflection with Stress Distribution", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Bending stress distribution
        ax = axes[0, 1]
        ax.fill_between(self.x, self.bending_stress, alpha=0.5, color='red')
        ax.plot(self.x, self.bending_stress, 'r-', linewidth=2)
        ax.set_xlabel("Position (m)", fontsize=11)
        ax.set_ylabel("Stress (Pa)", fontsize=11)
        ax.set_title("Bending Stress", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Moment diagram
        ax = axes[1, 0]
        colors = np.where(self.M >= 0, 'blue', 'red')
        ax.bar(self.x, self.M, width=self.x[1] - self.x[0], color=colors, alpha=0.7)
        ax.axhline(y=0, color='k', linewidth=1)
        ax.set_xlabel("Position (m)", fontsize=11)
        ax.set_ylabel("Moment (N·m)", fontsize=11)
        ax.set_title("Bending Moment Diagram", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # Shear force diagram
        ax = axes[1, 1]
        ax.fill_between(self.x, self.V, alpha=0.5, color='green')
        ax.plot(self.x, self.V, 'g-', linewidth=2)
        ax.set_xlabel("Position (m)", fontsize=11)
        ax.set_ylabel("Force (N)", fontsize=11)
        ax.set_title("Shear Force Diagram", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout(rect=[0, 0, 1, 0.97])
        return fig

    def create_deflection_plot(self) -> plt.Figure:
        """Create individual high-quality deflection plot."""
        fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
        ax.fill_between(self.x, self.v, alpha=0.3, color='blue')
        ax.plot(self.x, self.v, 'b-', linewidth=2.5, label='v(x)')
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, label='Original axis')
        ax.set_xlabel("Position x (m)", fontsize=12)
        ax.set_ylabel("Lateral Deflection v(x) (m)", fontsize=12)
        ax.set_title("Lateral Deflection Profile: v(x) from ODE Solution", fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)
        plt.tight_layout()
        return fig

    def create_moment_plot(self) -> plt.Figure:
        """Create individual high-quality moment diagram plot."""
        fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
        colors = np.where(self.M >= 0, 'blue', 'red')
        ax.bar(self.x, self.M, width=self.x[1] - self.x[0], color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
        ax.axhline(y=0, color='k', linewidth=1.5)
        ax.set_xlabel("Position x (m)", fontsize=12)
        ax.set_ylabel("Bending Moment M(x) (N·m)", fontsize=12)
        ax.set_title("Bending Moment Diagram: M(x) from dM/dx = V Integration", fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        return fig

    def create_shear_plot(self) -> plt.Figure:
        """Create individual high-quality shear force plot."""
        fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
        ax.fill_between(self.x, self.V, alpha=0.5, color='green')
        ax.plot(self.x, self.V, 'g-', linewidth=2.5)
        ax.axhline(y=0, color='k', linewidth=1.5)
        ax.set_xlabel("Position x (m)", fontsize=12)
        ax.set_ylabel("Shear Force V(x) (N)", fontsize=12)
        ax.set_title("Shear Force Diagram: V(x) Internal Shear Distribution", fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def create_bending_stress_plot(self) -> plt.Figure:
        """Create individual high-quality bending stress plot."""
        fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
        ax.fill_between(self.x, self.bending_stress / 1e6, alpha=0.5, color='red')
        ax.plot(self.x, self.bending_stress / 1e6, 'r-', linewidth=2.5)
        ax.set_xlabel("Position x (m)", fontsize=12)
        ax.set_ylabel("Bending Stress (MPa)", fontsize=12)
        ax.set_title("Bending Stress Distribution: σ_b(x) = M(x)·c/I", fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def create_stress_heatmap_plot(self) -> plt.Figure:
        """Create individual high-quality stress heatmap across beam cross-section."""
        fig, ax = plt.subplots(figsize=(12, 7), dpi=300)

        n_height = 20
        height_positions = np.linspace(-self.problem.section.height / 2,
                                       self.problem.section.height / 2, n_height)
        stress_2d = np.zeros((n_height, len(self.x)))
        for i, s in enumerate(self.bending_stress):
            stress_2d[:, i] = s * (height_positions / (self.problem.section.height / 2))

        im = ax.contourf(self.x, height_positions * 1000, stress_2d / 1e6, levels=20, cmap='RdYlBu_r')
        ax.contour(self.x, height_positions * 1000, stress_2d / 1e6, levels=5, colors='black', alpha=0.2, linewidths=0.5)

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Stress (MPa)", fontsize=11)
        ax.set_xlabel("Position along Beam (m)", fontsize=12)
        ax.set_ylabel("Distance from Neutral Axis (mm)", fontsize=12)
        ax.set_title("Bending Stress Heatmap: Cross-Section Variation", fontsize=13, fontweight='bold')
        plt.tight_layout()
        return fig

    def create_deflection_stress_plot(self) -> plt.Figure:
        """Create combined deflection and stress visualization."""
        fig, ax = plt.subplots(figsize=(12, 7), dpi=300)

        norm = Normalize(vmin=0, vmax=np.max(self.bending_stress))
        cmap = plt.cm.hot

        scatter = ax.scatter(self.x, self.v * 1000, c=self.bending_stress / 1e6, cmap=cmap, s=80, edgecolor='black', linewidth=0.5)
        ax.plot(self.x, self.v * 1000, 'k-', linewidth=1.5, alpha=0.5)
        ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
        ax.set_xlabel("Position (m)", fontsize=12)
        ax.set_ylabel("Deflection (mm)", fontsize=12)
        ax.set_title("Deflection with Stress Overlay", fontsize=13, fontweight='bold')
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Bending Stress (MPa)", fontsize=11)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def create_deflected_beam_plot(self) -> plt.Figure:
        """Create visual representation of deflected beam shape with stress coloring."""
        fig, ax = plt.subplots(figsize=(12, 7), dpi=300)

        # Normalize stress for color mapping
        norm = Normalize(vmin=np.min(self.bending_stress), vmax=np.max(self.bending_stress))
        cmap = plt.cm.RdYlBu_r  # Red for high stress, blue for low

        # Determine orientation
        is_vertical = self.problem.orientation == "vertical"

        if is_vertical:
            # Vertical beam: x-axis is vertical (gravity acts downward)
            for i in range(len(self.x) - 1):
                stress_val = (self.bending_stress[i] + self.bending_stress[i + 1]) / 2
                color = cmap(norm(stress_val))
                # Swap axes for vertical: position is y-axis, deflection is x-axis
                ax.plot(self.v[i:i + 2] * 1000, self.x[i:i + 2], linewidth=3, color=color)

            # Add original position (vertical line)
            ax.plot(np.zeros_like(self.x), self.x, 'k--', linewidth=1.5, alpha=0.3, label='Original position')

            # Draw fixed support at top
            h = self.problem.section.height
            rect = patches.Rectangle((-h / 2 * 1000, self.x[-1] - 0.01), h * 1000, 0.01,
                                     edgecolor='black', facecolor='gray', alpha=0.5)
            ax.add_patch(rect)

            # Add gravity arrow
            ax.arrow(self.x[-1] * 0.8 * 1000, 0.1, 0, -0.3, head_width=0.002, head_length=0.05,
                    fc='red', ec='red', linewidth=2, alpha=0.7)
            ax.text(self.x[-1] * 0.8 * 1000 + 0.01, 0.05, 'g', fontsize=12, color='red', fontweight='bold')

            ax.set_xlabel("Deflection (mm)", fontsize=12)
            ax.set_ylabel("Height along Beam (m)", fontsize=12)
            ax.set_title("Vertical Beam - Deflected Shape with Stress Distribution", fontsize=13, fontweight='bold')

        else:
            # Horizontal beam: standard plot
            for i in range(len(self.x) - 1):
                stress_val = (self.bending_stress[i] + self.bending_stress[i + 1]) / 2
                color = cmap(norm(stress_val))
                ax.plot(self.x[i:i + 2], self.v[i:i + 2] * 1000, linewidth=3, color=color)

            # Add original position
            ax.plot(self.x, np.zeros_like(self.x), 'k--', linewidth=1.5, alpha=0.3, label='Original position')

            # Draw section at fixed end
            h = self.problem.section.height
            rect = patches.Rectangle((self.x[-1] - 0.01, -h / 2 * 1000), 0.01, h * 1000,
                                     edgecolor='black', facecolor='gray', alpha=0.5)
            ax.add_patch(rect)

            ax.set_xlabel("Position along Beam (m)", fontsize=12)
            ax.set_ylabel("Deflection (mm)", fontsize=12)
            ax.set_title("Horizontal Beam - Deflected Shape with Stress Distribution", fontsize=13, fontweight='bold')

        # Colorbar
        sm = ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label("Bending Stress (MPa)", fontsize=11)

        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)
        plt.tight_layout()
        return fig

    def get_summary_stats(self) -> dict:
        """Return key analysis metrics."""
        return {
            'max_deflection': float(np.max(np.abs(self.v))),
            'max_bending_stress': float(np.max(self.bending_stress)),
            'max_axial_stress': float(np.max(self.axial_stress)),
            'max_moment': float(np.max(np.abs(self.M))),
            'max_shear': float(np.max(np.abs(self.V))),
            'total_bending_strain_energy': float(np.trapz(self.M**2 / (2 * self.problem.material.E * self.problem.section.moment_of_inertia), self.x)),
        }
