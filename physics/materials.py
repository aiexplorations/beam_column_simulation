"""
Material property definitions for beam-column simulations.
"""

from beam_column import Material


# Common engineering materials
STEEL = Material(
    E=200e9,  # Pa (Young's modulus)
    density=7850,  # kg/m³
    poisson_ratio=0.3
)

ALUMINUM = Material(
    E=69e9,  # Pa
    density=2700,  # kg/m³
    poisson_ratio=0.33
)

WOOD = Material(
    E=12e9,  # Pa (typical for softwood)
    density=500,  # kg/m³
    poisson_ratio=0.3
)

CONCRETE = Material(
    E=30e9,  # Pa
    density=2400,  # kg/m³
    poisson_ratio=0.2
)
