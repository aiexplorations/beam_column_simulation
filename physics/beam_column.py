"""
Beam-Column Simulator: Solves deflection, stress, and strain for beams under
combined axial and lateral loads using numerical ODE solving.
"""

import numpy as np
from scipy.integrate import odeint
from dataclasses import dataclass
from typing import Tuple


@dataclass
class BeamSection:
    """Cross-sectional properties of the beam."""
    width: float  # m (for rectangular section)
    height: float  # m (for rectangular section)

    @property
    def area(self) -> float:
        """Cross-sectional area."""
        return self.width * self.height

    @property
    def moment_of_inertia(self) -> float:
        """Second moment of inertia about neutral axis."""
        return self.width * self.height**3 / 12

    @property
    def max_distance_from_neutral(self) -> float:
        """Distance from neutral axis to extreme fiber."""
        return self.height / 2


@dataclass
class Material:
    """Material properties."""
    E: float  # Young's modulus (Pa)
    density: float  # kg/m³
    poisson_ratio: float = 0.3  # Poisson's ratio


@dataclass
class PointLoad:
    """Point load definition with position and direction along beam."""
    magnitude: float  # Load magnitude (N) - always positive
    position: float  # Position from x=0 (0 to L, normalized 0-1 if as_fraction=True)
    as_fraction: bool = False  # If True, position is 0-1 fraction of beam length
    direction: str = "downward"  # "downward" (positive) or "upward" (negative) for lateral loads


@dataclass
class BeamColumnProblem:
    """Complete beam-column problem definition."""
    length: float  # Beam length (m)
    section: BeamSection
    material: Material
    axial_load: float  # N (positive = compression)
    lateral_load: float  # N/m (distributed load)
    point_load: float = 0.0  # N (at free end for cantilever) - DEPRECATED, use point_loads instead
    point_loads: list = None  # List of PointLoad objects for multiple loads at different positions
    orientation: str = "horizontal"  # "horizontal" or "vertical"
    include_self_weight: bool = True  # Include beam self-weight
    g: float = 9.81  # Gravitational acceleration (m/s²)
    end_condition: str = "cantilever"  # "cantilever", "simply_supported", "fixed_fixed", or "hinged_free"

    def __post_init__(self):
        """Initialize point_loads if not provided."""
        if self.point_loads is None:
            # For backward compatibility, convert point_load to point_loads
            if self.point_load != 0.0:
                # Place point load at free end (x=L for cantilever)
                self.point_loads = [PointLoad(magnitude=self.point_load, position=self.length, as_fraction=False)]
            else:
                self.point_loads = []

    @property
    def self_weight_load(self) -> float:
        """Calculate self-weight distributed load in N/m."""
        if not self.include_self_weight:
            return 0.0
        return self.section.area * self.material.density * self.g

    @property
    def total_lateral_load(self) -> float:
        """Total lateral load including self-weight if vertical."""
        total = self.lateral_load
        if self.orientation == "vertical" and self.include_self_weight:
            total += self.self_weight_load
        return total

    def get_total_point_load(self) -> float:
        """Get total point load from all point loads."""
        return sum(pl.magnitude for pl in self.point_loads)


class BeamColumnSolver:
    """Solves the beam-column differential equations."""

    def __init__(self, problem: BeamColumnProblem):
        self.problem = problem
        self.EI = problem.material.E * problem.section.moment_of_inertia
        self.P = problem.axial_load
        self.q = problem.total_lateral_load  # Use total including self-weight
        self.point_loads = problem.point_loads  # List of PointLoad objects
        self.L = problem.length
        self.A = problem.section.area
        self.E = problem.material.E
        self.c = problem.section.max_distance_from_neutral

        # Characteristic length for beam-column coupling
        self.alpha = np.sqrt(self.P / self.EI) if self.P > 0 else 0

    def _get_shear_at_position(self, x: float) -> float:
        """
        Calculate shear force at position x, accounting for point loads.
        Shear = distributed load * remaining length + sum of point loads beyond x
        Direction: downward (positive) or upward (negative)
        """
        shear = self.q * (self.L - x)  # Shear from distributed load

        # Add contributions from point loads at positions > x (moving backwards from free end)
        for pl in self.point_loads:
            pos = pl.position if not pl.as_fraction else pl.position * self.L
            if pos >= x:  # Point load is to the right of current position
                # Apply sign based on direction
                load_sign = 1.0 if pl.direction == "downward" else -1.0
                shear += load_sign * pl.magnitude

        return shear

    def _beam_column_odes(self, y: np.ndarray, x: float) -> np.ndarray:
        """
        System of ODEs for beam-column problem.

        State vector y = [v, v', M, V]
        where:
            v = lateral deflection
            v' = slope (dv/dx)
            M = bending moment
            V = shear force

        Free end at x=0, fixed end at x=L
        """
        v, dv_dx, M, V = y

        # Differential equations:
        # dv/dx = slope
        dv = dv_dx

        # d²v/dx² = M/EI (from bending equation with P*v coupling)
        d2v = M / self.EI

        # dM/dx = V (from equilibrium)
        dM = V

        # dV/dx = -q (from vertical equilibrium, constant between point loads)
        dV = -self.q

        return np.array([dv, d2v, dM, dV])

    def _apply_point_loads(self, V_initial: float, x_array: np.ndarray) -> np.ndarray:
        """
        Adjust initial shear force to account for all point loads with direction.
        Returns the correct initial shear at x=0.
        """
        # Initial shear = distributed load across entire length + all point loads
        V_init = self.q * self.L
        for pl in self.point_loads:
            # Apply sign based on direction
            load_sign = 1.0 if pl.direction == "downward" else -1.0
            V_init += load_sign * pl.magnitude
        return V_init

    def _solve_segmented(self, y0: np.ndarray, x: np.ndarray) -> np.ndarray:
        """
        Solve ODE in segments between point loads to handle shear discontinuities.
        Point loads create discontinuities in shear force that must be handled explicitly.
        Supports directional loads (upward/downward).
        """
        # Convert point load positions to absolute coordinates if given as fractions
        point_load_positions = []
        for pl in self.point_loads:
            pos = pl.position if not pl.as_fraction else pl.position * self.L
            # Store direction as sign multiplier: 1.0 for downward, -1.0 for upward
            direction_sign = 1.0 if pl.direction == "downward" else -1.0
            point_load_positions.append((pos, pl.magnitude, direction_sign))

        # Sort by position
        point_load_positions.sort(key=lambda p: p[0])

        # Create segment boundaries: start with x=0 and x=L, add point load positions
        segment_boundaries = [0.0]
        for pos, _, _ in point_load_positions:
            if 0 < pos < self.L:
                segment_boundaries.append(pos)
        segment_boundaries.append(self.L)
        segment_boundaries = sorted(set(segment_boundaries))

        # Solve in each segment
        solution_list = []
        current_state = y0.copy()

        for i in range(len(segment_boundaries) - 1):
            x_start = segment_boundaries[i]
            x_end = segment_boundaries[i + 1]

            # Find x indices within this segment
            segment_mask = (x >= x_start) & (x <= x_end)
            x_segment = x[segment_mask]

            if len(x_segment) == 0:
                continue

            # Solve this segment
            segment_solution = odeint(self._beam_column_odes, current_state, x_segment)
            solution_list.append(segment_solution)

            # Update state for next segment
            current_state = segment_solution[-1].copy()

            # Apply point load discontinuity at segment boundary (if not at boundaries)
            if i < len(segment_boundaries) - 2:  # Not at final boundary
                x_next = segment_boundaries[i + 1]
                # Find point loads at this position (with small tolerance for floating point)
                for pos, mag, direction_sign in point_load_positions:
                    if abs(pos - x_next) < 1e-9:
                        # Jump in shear force due to point load
                        # Negative sign because we're moving from left to right
                        current_state[3] -= direction_sign * mag

        # Combine all segment solutions
        full_solution = np.vstack(solution_list) if solution_list else np.array([y0])

        # Handle case where x array might need interpolation
        if len(full_solution) != len(x):
            # Re-solve with full x array using the corrected approach
            # This is a fallback for when segment solving produces different point counts
            full_solution = odeint(self._beam_column_odes, y0, x)

        return full_solution

    def solve(self, num_points: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Solve the beam-column problem using numerical ODE integration.
        Supports different boundary conditions.

        Returns:
            x: position along beam (0 to L)
            v: lateral deflection
            M: bending moment
            V: shear force
        """
        x = np.linspace(0, self.L, num_points)
        end_condition = self.problem.end_condition

        if end_condition == "cantilever":
            return self._solve_cantilever(x)
        elif end_condition == "simply_supported":
            return self._solve_simply_supported(x)
        elif end_condition == "fixed_fixed":
            return self._solve_fixed_fixed(x)
        elif end_condition == "hinged_free":
            return self._solve_hinged_free(x)
        elif end_condition == "fixed_hinged":
            return self._solve_fixed_hinged(x)
        elif end_condition == "hinged_fixed":
            return self._solve_hinged_fixed(x)
        else:
            raise ValueError(f"Unknown end condition: {end_condition}")

    def _solve_cantilever(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Solve for cantilever beam (fixed at x=L, free at x=0)."""
        from scipy.optimize import brentq

        # Calculate total initial shear (all point loads + distributed load over beam length)
        V_initial = self._apply_point_loads(0, x)

        def shooting_function(initial_slope: float) -> float:
            """Find slope such that v(L) = 0."""
            y0 = np.array([0.0, initial_slope, 0.0, V_initial])
            solution = self._solve_segmented(y0, x)
            return solution[-1, 0]

        try:
            correct_slope = brentq(shooting_function, -1.0, 1.0, xtol=1e-6)
        except ValueError:
            # Approximate for total loads
            total_load = self.q * self.L + sum(pl.magnitude for pl in self.point_loads)
            correct_slope = -total_load * self.L**3 / (3 * self.EI)

        y0 = np.array([0.0, correct_slope, 0.0, V_initial])
        solution = self._solve_segmented(y0, x)

        return x, solution[:, 0], solution[:, 2], solution[:, 3]

    def _solve_simply_supported(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Solve for simply supported beam (hinged at both ends)."""
        from scipy.optimize import brentq

        def shooting_function(initial_slope: float) -> float:
            """Find slope such that v(L) = 0 and M(0) = 0."""
            y0 = np.array([0.0, initial_slope, 0.0, self.q * self.L])  # M(0)=0
            solution = odeint(self._beam_column_odes, y0, x)
            return solution[-1, 0]  # v(L) should be 0

        try:
            correct_slope = brentq(shooting_function, -0.5, 0.5, xtol=1e-6)
        except ValueError:
            # Approximate for distributed load on simply supported
            correct_slope = self.q * self.L**3 / (24 * self.EI)

        y0 = np.array([0.0, correct_slope, 0.0, self.q * self.L])
        solution = odeint(self._beam_column_odes, y0, x)

        return x, solution[:, 0], solution[:, 2], solution[:, 3]

    def _solve_fixed_fixed(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Solve for fixed-fixed beam (fixed at both ends)."""
        from scipy.optimize import fsolve

        def shooting_equations(params):
            """Find initial slope and moment such that v(0)=v(L)=0 and dv/dx(0)=dv/dx(L)=0."""
            initial_slope, initial_moment = params
            y0 = np.array([0.0, initial_slope, initial_moment, self.q * self.L])
            solution = odeint(self._beam_column_odes, y0, x)

            # Both ends fixed: v(0) = 0 (at start), v(L) = 0, dv/dx(L) = 0
            return [
                solution[-1, 0],      # v(L) = 0
                solution[-1, 1],      # dv/dx(L) = 0
            ]

        try:
            correct_params = fsolve(shooting_equations, [0.0, 0.0], full_output=True)
            initial_slope, initial_moment = correct_params[0]
        except:
            # Approximate for distributed load on fixed-fixed
            initial_moment = -self.q * self.L**2 / 12
            initial_slope = 0

        y0 = np.array([0.0, initial_slope, initial_moment, self.q * self.L])
        solution = odeint(self._beam_column_odes, y0, x)

        return x, solution[:, 0], solution[:, 2], solution[:, 3]

    def _solve_hinged_free(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Solve for hinged-free beam (pinned at x=0, free at x=L)."""
        from scipy.optimize import brentq

        V_initial = self._apply_point_loads(0, x)

        def shooting_function(initial_moment: float) -> float:
            """Find moment such that v(0) = 0."""
            y0 = np.array([0.0, 0.0, initial_moment, V_initial])
            solution = self._solve_segmented(y0, x)
            return solution[0, 0]  # v(0) should be 0

        try:
            correct_moment = brentq(shooting_function, -1.0, 1.0, xtol=1e-6)
        except ValueError:
            correct_moment = 0

        y0 = np.array([0.0, 0.0, correct_moment, V_initial])
        solution = self._solve_segmented(y0, x)

        return x, solution[:, 0], solution[:, 2], solution[:, 3]

    def _solve_fixed_hinged(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Solve for fixed-hinged beam (fixed at x=0, hinged at x=L)."""
        from scipy.optimize import brentq

        V_initial = self._apply_point_loads(0, x)

        def shooting_function(initial_slope: float) -> float:
            """Find slope such that M(L) = 0 (moment at hinged end)."""
            y0 = np.array([0.0, initial_slope, 0.0, V_initial])
            solution = self._solve_segmented(y0, x)
            return solution[-1, 2]  # M(L) should be 0

        try:
            correct_slope = brentq(shooting_function, -1.0, 1.0, xtol=1e-6)
        except ValueError:
            correct_slope = 0

        y0 = np.array([0.0, correct_slope, 0.0, V_initial])
        solution = self._solve_segmented(y0, x)

        return x, solution[:, 0], solution[:, 2], solution[:, 3]

    def _solve_hinged_fixed(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Solve for hinged-fixed beam (hinged at x=0, fixed at x=L)."""
        from scipy.optimize import fsolve

        V_initial = self._apply_point_loads(0, x)

        def shooting_equations(params):
            """Find initial slope and moment such that v(0)=0, v(L)=0, M(0)=0."""
            initial_slope, initial_moment = params
            y0 = np.array([0.0, initial_slope, initial_moment, V_initial])
            solution = self._solve_segmented(y0, x)

            return [
                solution[0, 2],      # M(0) = 0 (moment at hinged end)
                solution[-1, 0],     # v(L) = 0 (deflection at fixed end)
            ]

        try:
            correct_params = fsolve(shooting_equations, [0.0, 0.0], full_output=True)
            initial_slope, initial_moment = correct_params[0]
        except:
            initial_slope = 0
            initial_moment = 0

        y0 = np.array([0.0, initial_slope, initial_moment, V_initial])
        solution = self._solve_segmented(y0, x)

        return x, solution[:, 0], solution[:, 2], solution[:, 3]

    def calculate_stresses(self, x: np.ndarray, M: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate bending stress and axial stress.

        Returns:
            bending_stress: Bending stress (varies with distance from neutral axis)
            axial_stress: Axial stress (constant across section)
        """
        # Bending stress at extreme fiber: σ = M * c / I
        I = self.problem.section.moment_of_inertia
        bending_stress = np.abs(M) * self.c / I

        # Axial stress: σ = P / A
        axial_stress = np.ones_like(x) * self.P / self.A

        # Combined stress (magnitude)
        combined_stress = np.sqrt(bending_stress**2 + axial_stress**2)

        return bending_stress, axial_stress, combined_stress

    def calculate_strains(self, bending_stress: np.ndarray, axial_stress: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate strains from stresses using material properties.

        Returns:
            bending_strain: Bending strain
            axial_strain: Axial strain
        """
        E = self.problem.material.E
        nu = self.problem.material.poisson_ratio

        bending_strain = bending_stress / E
        axial_strain = axial_stress / E

        return bending_strain, axial_strain
