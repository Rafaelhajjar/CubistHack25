# Development Timeline: Manhattan Congestion Map

This timeline outlines the steps to build the interactive congestion map, based on the `project_overview.md`.

**Phase 1: Data Handling**

1.  **Load Data:**
    *   Create a Python script (e.g., `app.py` or a separate `data_loader.py`).
    *   Use Pandas `pd.read_csv()` to load `MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv`.
2.  **Initial Preprocessing:**
    *   Combine date/time columns (`Toll Date`, `Toll Hour`, etc.) into a single `datetime` column using `pd.to_datetime()`.
    *   Ensure `CRZ Entries` column is numeric using `pd.to_numeric()`.
3.  **Map Coordinates:**
    *   Define the `entry_points` dictionary.
    *   Create `latitude` and `longitude` columns by mapping `Detection Region` using the `entry_points` dictionary.
4.  **Handle Missing Coordinates:**
    *   Check for rows where the coordinate mapping failed (`df.isnull().sum()`).
    *   Decide and implement a strategy (e.g., drop these rows).
5.  **(Optional) Cache Data:**
    *   If using Streamlit, wrap the data loading and preprocessing steps in a function decorated with `@st.cache_data` to improve performance.

**Phase 2: Application Structure (Streamlit)**

6.  **Setup Streamlit App:**
    *   Ensure `streamlit` and `streamlit-folium` are installed (`pip install streamlit streamlit-folium`).
    *   Import necessary libraries (`streamlit as st`, `pandas as pd`, `folium`, `streamlit_folium`).
    *   Structure `app.py` with basic Streamlit elements (e.g., `st.title`).
7.  **Add UI Filters:**
    *   Use `st.sidebar.multiselect` to create filters for `Vehicle Class`, `Time Period`, and `Day of Week`. Populate options by getting unique values from the DataFrame (`df['column_name'].unique()`).
8.  **Add Time Slider:**
    *   Determine the appropriate range and step for the time slider (e.g., unique hours, unique 10-minute blocks, or timestamps).
    *   Use `st.slider` to create the time selection widget.

**Phase 3: Core Logic & Visualization**

9.  **Filter Data:**
    *   Read the current values from all sidebar filters and the time slider.
    *   Filter the main DataFrame based on these selections.
10. **Aggregate Filtered Data:**
    *   Group the *filtered* DataFrame by `latitude`, `longitude`, and the chosen time granularity (matching the slider's step).
    *   Calculate the sum of `CRZ Entries` for each group.
11. **Create Base Map:**
    *   Instantiate a Folium map centered on Manhattan: `m = folium.Map(...)`.
12. **Define Marker Scaling:**
    *   Create Python functions (`calculate_radius`, `calculate_color`) that take the aggregated `CRZ Entries` count and return appropriate radius and color values for markers.
13. **Plot Entry Points:**
    *   Iterate through the *aggregated* data for the selected time step.
    *   For each entry point, add a `folium.CircleMarker` to the map `m`, using the scaling functions for radius and color, and add a popup showing the entry count.
14. **Display Map:**
    *   Use `st_folium(m)` to render the generated Folium map in the Streamlit app.

**Phase 4: Refinement & Testing**

15. **Test Interactivity:**
    *   Run the app (`streamlit run app.py`).
    *   Thoroughly test the time slider and all filters to ensure the map updates correctly and efficiently.
16. **Refine Visualization:**
    *   Adjust map zoom, marker scaling functions (radius, color), and popups for clarity and visual appeal.
17. **Code Cleanup:**
    *   Organize code, add comments where necessary, and ensure efficient data handling. 