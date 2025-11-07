"""
FastAPI backend for Beam-Column Simulator.
Provides RESTful endpoints for solving beam-column problems and getting materials.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np
import traceback
import logging

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'physics'))

from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver, PointLoad
from visualizer import BeamVisualizer
import materials

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Beam-Column Simulator API",
    description="Numerical ODE solver for coupled beam-column analysis with P-Δ effects",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Material map
MATERIAL_MAP = {
    "Steel": materials.STEEL,
    "Aluminum": materials.ALUMINUM,
    "Wood": materials.WOOD,
    "Concrete": materials.CONCRETE
}

# End condition map
END_CONDITION_MAP = {
    "cantilever": "cantilever",
    "simply_supported": "simply_supported",
    "fixed_fixed": "fixed_fixed",
    "hinged_free": "hinged_free"
}


# Pydantic models for request/response validation
class MaterialInfo(BaseModel):
    name: str
    density: float
    youngs_modulus: float = Field(..., alias="E")
    yield_stress: float

    class Config:
        populate_by_name = True


class PointLoadData(BaseModel):
    magnitude: float = Field(..., gt=0, le=500, description="Magnitude in kN")
    position: float = Field(..., ge=0, le=1, description="Position as fraction (0-1)")
    direction: str = Field("downward", description="Direction: downward or upward")


class SolveProblemRequest(BaseModel):
    length: float = Field(..., gt=0, le=5, description="Beam length in meters")
    width: float = Field(..., gt=0, le=0.3, description="Section width in meters")
    height: float = Field(..., gt=0, le=0.3, description="Section height in meters")
    material: str = Field(..., description="Material: Steel, Aluminum, Wood, Concrete")
    orientation: str = Field("horizontal", description="horizontal or vertical")
    end_condition: str = Field("cantilever", description="Boundary condition type")
    axial_load: float = Field(0, ge=0, le=500, description="Axial load in kN")
    lateral_load: float = Field(0, ge=0, le=100, description="Lateral load in kN/m")
    include_self_weight: bool = Field(True, description="Include beam self-weight")
    point_loads: Optional[List[PointLoadData]] = Field(None, description="Optional point loads")


class SolutionSummary(BaseModel):
    max_deflection_mm: float
    max_bending_stress_mpa: float
    max_moment_knm: float
    max_shear_kn: float
    max_axial_stress_mpa: float
    critical_buckling_load_kn: float


class SolutionData(BaseModel):
    x: List[float]
    deflection: List[float]
    moment: List[float]
    shear: List[float]
    bending_stress: List[float]
    axial_stress: List[float]
    combined_stress: List[float]
    bending_strain: List[float]
    axial_strain: List[float]


class SolveProblemResponse(BaseModel):
    status: str
    data: SolutionData
    summary: SolutionSummary


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/materials")
async def get_materials():
    """Get available materials with their properties."""
    try:
        materials_list = []
        for name, material in MATERIAL_MAP.items():
            materials_list.append(
                MaterialInfo(
                    name=name,
                    density=float(material.density),
                    youngs_modulus=float(material.E),
                    yield_stress=float(material.E / 1000),  # Approximate yield stress
                )
            )
        return {"materials": materials_list}
    except Exception as e:
        logger.error(f"Error fetching materials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/solve", response_model=SolveProblemResponse)
async def solve_problem(request: SolveProblemRequest):
    """
    Solve beam-column problem with given parameters.

    Parameters:
    - **length**: Beam length in meters (0.5-5.0)
    - **width**: Section width in meters (0.01-0.3)
    - **height**: Section height in meters (0.01-0.3)
    - **material**: Material choice (Steel, Aluminum, Wood, Concrete)
    - **orientation**: Horizontal or vertical
    - **end_condition**: Cantilever, simply_supported, fixed_fixed, or hinged_free
    - **axial_load**: Axial compressive load in kN
    - **lateral_load**: Distributed lateral load in kN/m
    - **include_self_weight**: Include beam self-weight in analysis
    - **point_loads**: Optional list of point loads

    Returns:
    - Solution data with deflection, moment, shear, stresses
    - Summary statistics with max values
    """
    try:
        # Validate material
        if request.material not in MATERIAL_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown material: {request.material}"
            )

        # Validate orientation
        if request.orientation not in ["horizontal", "vertical"]:
            raise HTTPException(
                status_code=400,
                detail="Orientation must be horizontal or vertical"
            )

        # Validate end condition
        if request.end_condition not in END_CONDITION_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown end condition: {request.end_condition}"
            )

        # Get material
        material = MATERIAL_MAP[request.material]

        # Convert loads from kN to N
        axial_load_n = request.axial_load * 1000
        lateral_load_nm = request.lateral_load * 1000

        # Process point loads
        point_loads_list = []
        if request.point_loads:
            for pl in request.point_loads:
                if pl.magnitude > 0:
                    point_loads_list.append(
                        PointLoad(
                            magnitude=pl.magnitude * 1000,  # Convert kN to N
                            position=pl.position,
                            as_fraction=True,
                            direction=pl.direction
                        )
                    )

        # Create beam section and problem
        section = BeamSection(width=request.width, height=request.height)
        problem = BeamColumnProblem(
            length=request.length,
            section=section,
            material=material,
            axial_load=axial_load_n,
            lateral_load=lateral_load_nm,
            point_loads=point_loads_list if point_loads_list else None,
            orientation=request.orientation,
            include_self_weight=request.include_self_weight,
            end_condition=request.end_condition
        )

        # Solve the problem
        solver = BeamColumnSolver(problem)
        x, v, M, V = solver.solve(num_points=100)

        # Calculate stresses and strains
        bending_stress, axial_stress, combined_stress = solver.calculate_stresses(x, M)
        bending_strain, axial_strain = solver.calculate_strains(bending_stress, axial_stress)

        # Create visualizer for summary stats
        visualizer = BeamVisualizer(
            problem,
            x, v, M, V,
            bending_stress, axial_stress,
            bending_strain, axial_strain
        )
        stats = visualizer.get_summary_stats()

        # Calculate critical buckling load (Euler buckling)
        critical_buckling_load_kn = float(
            material.E *
            (np.pi ** 2) *
            section.moment_of_inertia /
            (request.length ** 2) / 1000
        )

        # Build response
        return SolveProblemResponse(
            status="success",
            data=SolutionData(
                x=x.tolist(),
                deflection=v.tolist(),
                moment=M.tolist(),
                shear=V.tolist(),
                bending_stress=bending_stress.tolist(),
                axial_stress=axial_stress.tolist(),
                combined_stress=combined_stress.tolist(),
                bending_strain=bending_strain.tolist(),
                axial_strain=axial_strain.tolist(),
            ),
            summary=SolutionSummary(
                max_deflection_mm=float(stats["max_deflection"] * 1000),
                max_bending_stress_mpa=float(stats["max_bending_stress"] / 1e6),
                max_moment_knm=float(stats["max_moment"] / 1000),
                max_shear_kn=float(stats["max_shear"] / 1000),
                max_axial_stress_mpa=float(stats["max_axial_stress"] / 1e6),
                critical_buckling_load_kn=critical_buckling_load_kn,
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Solver error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Solver error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    uvicorn.run(app, host="0.0.0.0", port=port)
