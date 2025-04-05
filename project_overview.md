# Project Overview: Manhattan Congestion Heatmap

## Goal
To create an interactive heatmap visualization of vehicle entries into Manhattan's Congestion Relief Zone (CRZ), based on the provided MTA data.

## Data
- **Source:** `MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv`
- **Schema:** Includes `Toll Date`, `Toll Hour`, `Time Period`, `Vehicle Class`, `Detection Region`, `CRZ Entries`, etc.
- **Entry Points:** Known coordinates for major Manhattan entry points.

## Roadmap

1.  **Data Loading & Preprocessing:**
    *   Load the CSV data using Pandas: `df = pd.read_csv('MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv')`.
    *   Combine date and time info: Create a single datetime column using `pd.to_datetime`, possibly by combining `Toll Date`, `Toll Hour`, `Toll 10 Minute Block`, or `Minute of Hour` as needed for the desired granularity.
    *   Map `Detection Region` to coordinates: Create new `latitude` and `longitude` columns by mapping the `Detection Region` string to the coordinates provided in the `entry_points` dictionary. Example: `df['latitude'] = df['Detection Region'].map(lambda x: entry_points.get(x, (None, None))[0])`.
    *   Handle potential missing data/coordinates: Check for rows where mapping failed (`df.isnull().sum()`) and decide on a strategy (e.g., drop rows, impute).
    *   Check data types: Ensure `CRZ Entries` is numeric (`pd.to_numeric`).

2.  **Data Aggregation:**
    *   Define time granularity: Decide if the slider will operate on hours, days, etc. The datetime column from Step 1 should reflect this.
    *   Group data: Use `df.groupby(['latitude', 'longitude', pd.Grouper(key='datetime_column', freq='H')])` (adjust `freq` as needed, e.g., '10min', 'D'). Include other filterable columns (`Vehicle Class`, `Time Period`, `Day of Week`) in the groupby if filtering happens *before* aggregation, or filter the grouped result.
    *   Aggregate `CRZ Entries`: Apply `.sum()` to the grouped object: `aggregated_df = grouped_df['CRZ Entries'].sum().reset_index()`.

3.  **Entry Point Visualization (using Folium):**
    *   Create base map: `m = folium.Map(location=[40.75, -73.98], zoom_start=12)` (center on Manhattan).
    *   Filter aggregated data: Select the data subset corresponding to the current state of the time slider and other filters.
    *   Plot entry points: Iterate through the *filtered* `aggregated_df`. For each entry point (lat/lon), add a marker: `folium.CircleMarker(location=[lat, lon], radius=calculate_radius(entries), color=calculate_color(entries), fill=True, fill_color=calculate_color(entries), popup=f'Entries: {entries}').add_to(m)`.
    *   Define scaling functions: Create `calculate_radius` and `calculate_color` functions to map the `CRZ Entries` volume to visual properties (e.g., logarithmic scaling for radius, color gradient for intensity).

4.  **Interactivity (using Streamlit):**
    *   Build UI layout: Use `st.slider` for the time selection. Determine the min/max range from the data's datetime column. The slider could represent hours of the day, or index into a sorted list of unique timestamps.
    *   Add filters: Use `st.sidebar.multiselect` for `Vehicle Class`, `Time Period`, and `Day of Week`. Get unique values from the original DataFrame for filter options.
    *   Connect UI to data: In the main script logic, read the values from the slider and multiselect widgets.
    *   Filter DataFrame: Apply filters to the *original* DataFrame `df` based on the selected UI values *before* performing the aggregation (Step 2) and visualization (Step 3) for the current view.
    *   Display map: Use `st_folium(m)` (requires `streamlit-folium` library) to render the dynamically generated Folium map `m`.

5.  **Web Application (Deployment with Streamlit):**
    *   Structure code: Create a main script (e.g., `app.py`). Import Pandas, Folium, Streamlit, and streamlit-folium.
    *   Load data: Load the preprocessed data (or run preprocessing steps) at the start of the script. Consider caching (`@st.cache_data`) the data loading/preprocessing for performance.
    *   Implement UI: Define the sidebar filters and the main area for the map.
    *   Implement logic: Write the filtering, aggregation, and map generation logic, triggered by changes in the UI widgets.
    *   Run app: Execute `streamlit run app.py` in the terminal.

## Technologies
- **Python:**
    - Pandas: Data manipulation.
    - Folium: Map/heatmap generation.
    - Flask / Streamlit: Web framework.
- **JavaScript (Optional - if using Leaflet directly):**
    - Leaflet.js: Mapping library.
    - Leaflet.heat: Heatmap plugin.

## Entry Point Coordinates

```python
entry_points = {
    "Brooklyn Bridge": (40.7061, -73.9969),
    "Queensboro Bridge": (40.7570, -73.9543),
    "Queens Midtown Tunnel": (40.7440, -73.9713),
    "West Side Highway at 60th St": (40.7713, -73.9916),
    "West 60th St": (40.7690, -73.9851),
    "Manhattan Bridge": (40.7075, -73.9903),
    "Lincoln Tunnel": (40.7608, -74.0021),
    "Holland Tunnel": (40.7256, -74.0119),
    "FDR Drive at 60th St": (40.7625, -73.9595),
    "FDR Drive at 34th St": (40.7448, -73.9721)
}
``` 