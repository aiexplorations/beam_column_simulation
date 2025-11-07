"""
Interactive Beam-Column Simulator Dashboard using Streamlit.
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from beam_column import BeamSection, BeamColumnProblem, BeamColumnSolver, PointLoad
from visualizer import BeamVisualizer
import materials


# Page configuration
st.set_page_config(
    page_title="Beam-Column Simulator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🏗️ Beam-Column Simulator")
st.markdown("*Numerical ODE solver for coupled beam-column analysis with P-Δ effects*")

# Sidebar: Input Parameters
st.sidebar.header("Problem Parameters")

# Beam geometry
st.sidebar.subheader("Geometry")
length = st.sidebar.slider("Beam Length (m)", 0.5, 5.0, 2.0, 0.1)
width = st.sidebar.slider("Section Width (m)", 0.01, 0.3, 0.1, 0.01)
height = st.sidebar.slider("Section Height (m)", 0.01, 0.3, 0.1, 0.01)

# Material properties
st.sidebar.subheader("Material")
material_choice = st.sidebar.selectbox(
    "Select Material",
    ["Steel", "Aluminum", "Wood", "Concrete"]
)
material_map = {
    "Steel": materials.STEEL,
    "Aluminum": materials.ALUMINUM,
    "Wood": materials.WOOD,
    "Concrete": materials.CONCRETE
}
selected_material = material_map[material_choice]

# Beam configuration
st.sidebar.subheader("Beam Configuration")

# Orientation
orientation = st.sidebar.radio(
    "Orientation",
    ["Horizontal", "Vertical"],
    horizontal=True
)
orientation_str = "horizontal" if orientation == "Horizontal" else "vertical"

# End conditions
end_condition = st.sidebar.selectbox(
    "End Conditions (Support Type)",
    ["Cantilever (Fixed-Free)", "Simply Supported (Hinged-Hinged)",
     "Fixed-Fixed (Both Fixed)", "Hinged-Free (Pinned-Free)"],
    help="Select the boundary conditions at beam ends"
)

end_condition_map = {
    "Cantilever (Fixed-Free)": "cantilever",
    "Simply Supported (Hinged-Hinged)": "simply_supported",
    "Fixed-Fixed (Both Fixed)": "fixed_fixed",
    "Hinged-Free (Pinned-Free)": "hinged_free"
}
end_condition_str = end_condition_map[end_condition]

# Self-weight option
include_self_weight = st.sidebar.checkbox("Include Self-Weight", value=True)

# Loading conditions
st.sidebar.subheader("Applied Loads")
axial_load = st.sidebar.slider(
    "Axial Compressive Load (kN)",
    0.0, 500.0, 50.0, 10.0
)
axial_load_n = axial_load * 1000  # Convert to Newtons

lateral_load = st.sidebar.slider(
    "Distributed Lateral Load (kN/m)",
    0.0, 100.0, 10.0, 1.0
)
lateral_load_n = lateral_load * 1000  # Convert to N/m

# Point loads configuration
st.sidebar.subheader("Point Loads (Optional)")
st.sidebar.markdown("*Add concentrated loads at specific positions along the beam*")

# Initialize session state for point loads
if 'num_point_loads' not in st.session_state:
    st.session_state.num_point_loads = 0
if 'point_loads_data' not in st.session_state:
    st.session_state.point_loads_data = []

# Control for number of point loads
num_loads_cols = st.sidebar.columns([2, 1])
with num_loads_cols[0]:
    new_num_loads = st.number_input(
        "Number of Point Loads",
        min_value=0, max_value=5, value=st.session_state.num_point_loads,
        step=1, key='num_point_loads_input'
    )
    if new_num_loads != st.session_state.num_point_loads:
        st.session_state.num_point_loads = new_num_loads
        if new_num_loads > len(st.session_state.point_loads_data):
            # Add new empty loads
            for i in range(new_num_loads - len(st.session_state.point_loads_data)):
                st.session_state.point_loads_data.append({'magnitude': 5.0, 'position_pct': 50.0})
        else:
            # Remove excess loads
            st.session_state.point_loads_data = st.session_state.point_loads_data[:new_num_loads]

# Configure each point load
point_loads_list = []
for i in range(st.session_state.num_point_loads):
    with st.sidebar.expander(f"Point Load {i+1}", expanded=(i==0)):
        cols = st.columns(2)
        with cols[0]:
            magnitude = st.slider(
                "Magnitude (kN)",
                0.0, 100.0,
                value=st.session_state.point_loads_data[i].get('magnitude', 5.0),
                step=0.5,
                key=f"pl_mag_{i}"
            )
            st.session_state.point_loads_data[i]['magnitude'] = magnitude

        with cols[1]:
            position_pct = st.slider(
                "Position (% from free end)",
                0.0, 100.0,
                value=st.session_state.point_loads_data[i].get('position_pct', 50.0),
                step=5.0,
                key=f"pl_pos_{i}"
            )
            st.session_state.point_loads_data[i]['position_pct'] = position_pct

        # Direction selection - context-aware for orientation
        current_orientation_key = f"pl_orient_{i}"
        if current_orientation_key not in st.session_state:
            st.session_state[current_orientation_key] = orientation

        orientation_changed = st.session_state[current_orientation_key] != orientation
        if orientation_changed:
            st.session_state[current_orientation_key] = orientation
            st.session_state.point_loads_data[i]['direction'] = 'downward'

        if orientation == "Horizontal":
            direction_options = ["Down ⬇️", "Up ⬆️"]
            direction_map = {"Down ⬇️": "downward", "Up ⬆️": "upward"}
            label_text = "Vertical Direction"
        else:
            direction_options = ["Right →", "Left ←"]
            direction_map = {"Right →": "downward", "Left ←": "upward"}
            label_text = "Horizontal Direction"

        current_direction = st.session_state.point_loads_data[i].get('direction', 'downward')
        if orientation == "Horizontal":
            current_label = "Down ⬇️" if current_direction == "downward" else "Up ⬆️"
        else:
            current_label = "Right →" if current_direction == "downward" else "Left ←"

        try:
            default_index = direction_options.index(current_label)
        except ValueError:
            default_index = 0

        direction = st.radio(
            label_text,
            direction_options,
            horizontal=True,
            index=default_index,
            key=f"pl_dir_{i}"
        )
        direction_str = direction_map[direction]
        st.session_state.point_loads_data[i]['direction'] = direction_str

        if magnitude > 0:
            point_loads_list.append(
                PointLoad(
                    magnitude=magnitude * 1000,
                    position=position_pct / 100.0,
                    as_fraction=True,
                    direction=direction_str
                )
            )

# Solve button
st.sidebar.markdown("---")
if st.sidebar.button("🔧 Solve Problem", use_container_width=True):
    st.session_state.solve = True
else:
    st.session_state.solve = False

# Create problem definition
section = BeamSection(width=width, height=height)
problem = BeamColumnProblem(
    length=length,
    section=section,
    material=selected_material,
    axial_load=axial_load_n,
    lateral_load=lateral_load_n,
    point_loads=point_loads_list if point_loads_list else None,
    orientation=orientation_str,
    include_self_weight=include_self_weight,
    end_condition=end_condition_str
)

# Solve
if st.session_state.solve or 'solution' in st.session_state:
    if st.session_state.solve:
        with st.spinner("Solving beam-column equations..."):
            solver = BeamColumnSolver(problem)
            x, v, M, V = solver.solve(num_points=100)
            bending_stress, axial_stress, combined_stress = solver.calculate_stresses(x, M)
            bending_strain, axial_strain = solver.calculate_strains(bending_stress, axial_stress)

            st.session_state.solution = {
                'x': x, 'v': v, 'M': M, 'V': V,
                'bending_stress': bending_stress,
                'axial_stress': axial_stress,
                'combined_stress': combined_stress,
                'bending_strain': bending_strain,
                'axial_strain': axial_strain,
            }

    sol = st.session_state.solution

    visualizer = BeamVisualizer(
        problem,
        sol['x'], sol['v'], sol['M'], sol['V'],
        sol['bending_stress'], sol['axial_stress'],
        sol['bending_strain'], sol['axial_strain']
    )

    # Display results
    st.header("Analysis Results")

    stats = visualizer.get_summary_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Max Deflection", f"{stats['max_deflection']*1000:.2f} mm")
    with col2:
        st.metric("Max Stress", f"{stats['max_bending_stress']/1e6:.1f} MPa")
    with col3:
        st.metric("Max Moment", f"{stats['max_moment']/1000:.2f} kN·m")
    with col4:
        st.metric("Max Shear", f"{stats['max_shear']/1000:.2f} kN")

    # Visualization tabs
    tab1, tab2, tab3 = st.tabs(["Charts", "Summary", "Data"])

    with tab1:
        fig = visualizer.create_deflected_beam_plot()
        st.pyplot(fig, width='stretch')

        col1, col2 = st.columns(2)
        with col1:
            fig = visualizer.create_deflection_plot()
            st.pyplot(fig, width='stretch')
        with col2:
            fig = visualizer.create_moment_plot()
            st.pyplot(fig, width='stretch')

        col1, col2 = st.columns(2)
        with col1:
            fig = visualizer.create_shear_plot()
            st.pyplot(fig, width='stretch')
        with col2:
            fig = visualizer.create_bending_stress_plot()
            st.pyplot(fig, width='stretch')

        fig = visualizer.create_stress_heatmap_plot()
        st.pyplot(fig, width='stretch')

    with tab2:
        fig = visualizer.create_simple_plot()
        st.pyplot(fig, width='stretch')

    with tab3:
        import pandas as pd
        results_df = {
            'Position (m)': sol['x'],
            'Deflection (mm)': sol['v'] * 1000,
            'Moment (kN·m)': sol['M'] / 1000,
            'Shear (kN)': sol['V'] / 1000,
            'Bending Stress (MPa)': sol['bending_stress'] / 1e6,
            'Axial Stress (MPa)': sol['axial_stress'] / 1e6,
        }
        df = pd.DataFrame(results_df)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Results (CSV)",
            data=csv,
            file_name="beam_column_results.csv",
            mime="text/csv"
        )

else:
    st.info("👈 Adjust parameters in the sidebar and click **Solve Problem** to begin analysis.")
