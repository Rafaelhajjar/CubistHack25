import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMapWithTime, MarkerCluster
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask import Flask
import plotly.express as px
import plotly.graph_objects as go
from dash_extensions.enrich import Output, Input, State
from datetime import datetime, timedelta

# Setup Flask server and Dash app
server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Manhattan Congestion Analytics'

# Entry Point Coordinates (Step 3 Part 1)
# Updated keys to match EXACTLY what's in the 'Detection Region' column
entry_points = {
    "Brooklyn": (40.7061, -73.9969),            # Brooklyn Bridge location
    "Queens": (40.7570, -73.9543),              # Queensboro Bridge location
    "Queens Midtown Tunnel": (40.7440, -73.9713), # In case this exact name appears
    "West Side Highway": (40.7713, -73.9916),   # West Side Highway at 60th St location
    "West 60th St": (40.7690, -73.9851),        # This one matched before
    "Manhattan Bridge": (40.7075, -73.9903),    # In case this exact name appears
    "Lincoln Tunnel": (40.7608, -74.0021),      # In case this exact name appears
    "Holland Tunnel": (40.7256, -74.0119),      # In case this exact name appears
    "FDR Drive": (40.7625, -73.9595),           # FDR Drive at 60th St location
    "East 60th St": (40.7625, -73.9595),        # Adding this one that appeared in unmapped
    "New Jersey": (40.7608, -74.0021),           # Using Lincoln Tunnel coordinates for New Jersey
    
    # Adding missing entries and alternate names
    "Brooklyn Battery Tunnel": (40.7001, -74.0145),  # Hugh L. Carey Tunnel
    "Battery Tunnel": (40.7001, -74.0145),
    "Hugh L. Carey Tunnel": (40.7001, -74.0145),
    "Williamsburg Bridge": (40.7131, -73.9722),
    
    # Add alternate names for existing tunnels/bridges
    "Brooklyn Bridge": (40.7061, -73.9969),
    "Manhattan": (40.7075, -73.9903),   # In case Manhattan Bridge is just called Manhattan
    "Queensboro Bridge": (40.7570, -73.9543),
    "Queens Tunnel": (40.7440, -73.9713),  # In case Queens Midtown Tunnel is called Queens Tunnel
    "Midtown Tunnel": (40.7440, -73.9713),
    "Holland": (40.7256, -74.0119),    # In case Holland Tunnel is just called Holland
    
    # Add more potential variants
    "Brooklyn Tunnel": (40.7001, -74.0145),
    "Williamsburg": (40.7131, -73.9722)   # In case Williamsburg Bridge is just called Williamsburg
}

# Function to load and process data
def load_and_process_data():
    try:
        # Load the dataset
        csv_file_path = 'MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv'
        df = pd.read_csv(csv_file_path)
        print("CSV file loaded successfully.")

        # --- Data Preprocessing ---
        # Convert to datetime
        df['datetime'] = pd.to_datetime(df['Toll 10 Minute Block'], errors='coerce')
        df.dropna(subset=['datetime'], inplace=True)
        
        # Convert 'CRZ Entries' to numeric
        df['CRZ Entries'] = pd.to_numeric(df['CRZ Entries'], errors='coerce')
        df.dropna(subset=['CRZ Entries'], inplace=True)
        df['CRZ Entries'] = df['CRZ Entries'].astype(int)
        
        # Add day/hour columns for easier filtering
        df['day_of_week'] = df['datetime'].dt.day_name()
        df['hour_of_day'] = df['datetime'].dt.hour
        df['date'] = df['datetime'].dt.date
        
        # Map coordinates
        # Create a mapping dictionary for faster lookups
        clean_entry_points = {key.strip(): coords for key, coords in entry_points.items()}
        
        lat_map = {name: coords[0] for name, coords in clean_entry_points.items()}
        lon_map = {name: coords[1] for name, coords in clean_entry_points.items()}

        df['Detection Region'] = df['Detection Region'].str.strip()
        df['latitude'] = df['Detection Region'].map(lat_map)
        df['longitude'] = df['Detection Region'].map(lon_map)
        
        # Drop rows without coordinates
        df.dropna(subset=['latitude', 'longitude'], inplace=True)
        
        return df
    except Exception as e:
        print(f"Error processing data: {e}")
        return pd.DataFrame()  # Return empty dataframe on error

# Load the data
df = load_and_process_data()

# For debugging:
print(f"Loaded data shape: {df.shape}")
    
# Define helper functions for analytics
def get_hourly_totals(dataframe):
    """Get total entries by hour of day"""
    return dataframe.groupby('hour_of_day')['CRZ Entries'].sum().reset_index()

def get_daily_totals(dataframe):
    """Get total entries by day of week"""
    return dataframe.groupby('day_of_week')['CRZ Entries'].sum().reset_index()

def get_region_totals(dataframe):
    """Get total entries by detection region"""
    return dataframe.groupby('Detection Region')['CRZ Entries'].sum().reset_index()

def get_vehicle_class_totals(dataframe):
    """Get total entries by vehicle class"""
    return dataframe.groupby('Vehicle Class')['CRZ Entries'].sum().reset_index()

def get_time_period_totals(dataframe):
    """Get total entries by time period"""
    return dataframe.groupby('Time Period')['CRZ Entries'].sum().reset_index()

def generate_heatmap_data(filtered_df):
    """Generate data for the heatmap"""
    # Group data by hour and location, then sum entries
    df_heatmap = filtered_df[['datetime', 'latitude', 'longitude', 'CRZ Entries']].copy()
    df_heatmap.dropna(inplace=True)

    # Group by hour for time-based visualization
    df_heatmap['hour'] = df_heatmap['datetime'].dt.floor('H')
    heatmap_data = df_heatmap.groupby(['hour', 'latitude', 'longitude'])['CRZ Entries'].sum().reset_index()

    # Format data for HeatMapWithTime (list of lists for each time step)
    time_index = sorted(heatmap_data['hour'].unique())
    data_for_heatmap = []
    
    for hour in time_index:
        hourly_data = heatmap_data[heatmap_data['hour'] == hour][['latitude', 'longitude', 'CRZ Entries']].values.tolist()
        data_for_heatmap.append(hourly_data)

    return data_for_heatmap, [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in time_index]

def create_map(filtered_df, map_type='heatmap'):
    """Create the folium map based on filtered data"""
    # Create base map centered around Manhattan
    map_center = [40.7831, -73.9712]
    m = folium.Map(location=map_center, zoom_start=12, tiles='CartoDB positron')
    
    if map_type == 'heatmap':
        # Create heatmap data
        heatmap_data, time_index = generate_heatmap_data(filtered_df)
        
        if heatmap_data:
            # Create HeatMapWithTime layer
            heatmap_wt = HeatMapWithTime(
                data=heatmap_data,
                index=time_index,
                gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'},
                min_opacity=0.1,
                max_opacity=0.7,
                radius=100,  # Adjust radius as needed
                use_local_extrema=True,
                auto_play=True,
                display_index=True
            )
            # Add heatmap layer to the map
            m.add_child(heatmap_wt)

    elif map_type == 'markers':
        # Group by region for marker visualization
        marker_data = filtered_df.groupby(['Detection Region', 'latitude', 'longitude'])['CRZ Entries'].sum().reset_index()
        
        # Create marker cluster
        marker_cluster = MarkerCluster().add_to(m)
        
        # Add markers for each entry point
        for _, row in marker_data.iterrows():
            # Scale marker size based on entry count
            radius = min(25, max(5, np.log1p(row['CRZ Entries']) * 3))
            
            # Create marker popup content
            popup_content = f"""
            <div style="width: 200px">
                <h4>{row['Detection Region']}</h4>
                <p><b>Total Entries:</b> {int(row['CRZ Entries'])}</p>
            </div>
            """
            
            # Add marker to map
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=radius,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(marker_cluster)
    
    # Save the map to a temporary HTML file that will be loaded in the Dash app
    map_path = 'temp_map.html'
    m.save(map_path)
    return map_path

# Create layout components
def generate_time_series_chart(filtered_df, interval='day'):
    """Generate time series chart of entries"""
    if interval == 'day':
        # Group by day
        df_grouped = filtered_df.groupby(filtered_df['datetime'].dt.date)['CRZ Entries'].sum().reset_index()
        df_grouped.columns = ['date', 'entries']
        
        fig = px.line(
            df_grouped, 
            x='date', 
            y='entries', 
            title='Daily Congestion Entries',
            labels={'date': 'Date', 'entries': 'Total Entries'}
        )
    else:
        # Group by hour
        df_grouped = filtered_df.groupby(filtered_df['datetime'].dt.floor('H'))['CRZ Entries'].sum().reset_index()
        df_grouped.columns = ['datetime', 'entries']
        
        fig = px.line(
            df_grouped, 
            x='datetime', 
            y='entries', 
            title='Hourly Congestion Entries',
            labels={'datetime': 'Time', 'entries': 'Total Entries'}
        )
    
    # Customize layout
    fig.update_layout(
        template='plotly_white',
        xaxis_title='Time',
        yaxis_title='Total Entries',
        hovermode='x unified'
    )
    
    return fig

def generate_vehicle_class_chart(filtered_df):
    """Generate bar chart of entries by vehicle class"""
    df_grouped = filtered_df.groupby('Vehicle Class')['CRZ Entries'].sum().reset_index()
    df_grouped = df_grouped.sort_values('CRZ Entries', ascending=False)
    
    fig = px.bar(
        df_grouped, 
        x='Vehicle Class', 
        y='CRZ Entries', 
        title='Entries by Vehicle Class',
        color='CRZ Entries',
        color_continuous_scale='Viridis'
    )
    
    # Customize layout
    fig.update_layout(
        template='plotly_white',
        xaxis_title='Vehicle Class',
        yaxis_title='Total Entries',
        xaxis={'categoryorder':'total descending'}
    )
    
    return fig

def generate_region_chart(filtered_df):
    """Generate bar chart of entries by detection region"""
    df_grouped = filtered_df.groupby('Detection Region')['CRZ Entries'].sum().reset_index()
    df_grouped = df_grouped.sort_values('CRZ Entries', ascending=False)
    
    fig = px.bar(
        df_grouped, 
        x='Detection Region', 
        y='CRZ Entries', 
        title='Entries by Detection Region',
        color='CRZ Entries',
        color_continuous_scale='Viridis'
    )
    
    # Customize layout
    fig.update_layout(
        template='plotly_white',
        xaxis_title='Detection Region',
        yaxis_title='Total Entries',
        xaxis={'categoryorder':'total descending'}
    )
    
    return fig

# Create the app layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Manhattan Congestion Analytics Dashboard", className="text-center my-4"),
            html.P("Analyze and visualize traffic congestion patterns in Manhattan's Congestion Relief Zone", 
                  className="text-center text-muted mb-5")
        ], width=12)
    ]),
    
    dbc.Row([
        # Sidebar for filters
        dbc.Col([
            html.H4("Filters", className="mb-3"),
            
            html.Label("Date Range:"),
            dcc.DatePickerRange(
                id='date-picker',
                min_date_allowed=df['datetime'].min().date() if not df.empty else None,
                max_date_allowed=df['datetime'].max().date() if not df.empty else None,
                start_date=df['datetime'].min().date() if not df.empty else None,
                end_date=df['datetime'].max().date() if not df.empty else None,
                className="mb-3"
            ),
            
            html.Label("Time of Day:"),
            dcc.RangeSlider(
                id='time-slider',
                min=0,
                max=23,
                step=1,
                marks={i: f'{i}:00' for i in range(0, 24, 3)},
                value=[0, 23],
                className="mb-3"
            ),
            
            html.Label("Vehicle Class:"),
            dcc.Dropdown(
                id='vehicle-class-dropdown',
                options=[{'label': cls, 'value': cls} for cls in df['Vehicle Class'].unique()] if not df.empty else [],
                multi=True,
                placeholder="Select vehicle class(es)",
                className="mb-3"
            ),
            
            html.Label("Day of Week:"),
            dcc.Dropdown(
                id='day-dropdown',
                options=[{'label': day, 'value': day} for day in sorted(df['day_of_week'].unique())] if not df.empty else [],
                multi=True,
                placeholder="Select day(s) of week",
                className="mb-3"
            ),
            
            html.Label("Detection Region:"),
            dcc.Dropdown(
                id='region-dropdown',
                options=[{'label': region, 'value': region} for region in sorted(df['Detection Region'].unique())] if not df.empty else [],
                multi=True,
                placeholder="Select detection region(s)",
                className="mb-3"
            ),
            
            html.Label("Map Type:"),
            dcc.RadioItems(
                id='map-type',
                options=[
                    {'label': 'Heatmap', 'value': 'heatmap'},
                    {'label': 'Markers', 'value': 'markers'}
                ],
                value='heatmap',
                className="mb-3"
            ),
            
            dbc.Button("Apply Filters", id="apply-button", color="primary", className="w-100 mb-4")
        ], width=3, className="bg-light p-4 border rounded"),
        
        # Main content area
        dbc.Col([
            dbc.Tabs([
                dbc.Tab([
                    html.Div(
                        id="map-container",
                        className="ratio ratio-16x9 p-2",
                        children=[
                            html.Iframe(id="map-iframe", style={"border": "none", "width": "100%", "height": "100%"})
                        ]
                    )
                ], label="Map View", tab_id="map-tab"),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id="time-series-chart")
                        ], width=12, className="mb-4"),
                        
                        dbc.Row([
                            dbc.Col([
                                dcc.RadioItems(
                                    id='time-interval',
                                    options=[
                                        {'label': 'Daily View', 'value': 'day'},
                                        {'label': 'Hourly View', 'value': 'hour'}
                                    ],
                                    value='day',
                                    className="mb-3"
                                )
                            ], width=12)
                        ]),
                        
                        dbc.Col([
                            dcc.Graph(id="vehicle-class-chart")
                        ], width=6),
                        
                        dbc.Col([
                            dcc.Graph(id="region-chart")
                        ], width=6)
                    ])
                ], label="Analytics", tab_id="analytics-tab"),
                
                dbc.Tab([
                    html.H3("Congestion Insights", className="mt-4 mb-3"),
                    html.Div(id="insights-container", className="p-3 bg-white rounded shadow-sm")
                ], label="Insights", tab_id="insights-tab"),
            ], id="tabs", active_tab="map-tab")
        ], width=9)
    ], className="g-0"),
    
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P("Manhattan Congestion Analytics Dashboard | Hackathon 2025", className="text-center text-muted")
        ], width=12)
    ], className="mt-4"),
    
    # Store component for keeping state
    dcc.Store(id='filtered-data')
], fluid=True)

# Callbacks
@app.callback(
    [Output("map-iframe", "src"),
     Output("time-series-chart", "figure"),
     Output("vehicle-class-chart", "figure"),
     Output("region-chart", "figure"),
     Output("insights-container", "children")],
    [Input("apply-button", "n_clicks"),
     Input("time-interval", "value")],
    [State("date-picker", "start_date"),
     State("date-picker", "end_date"),
     State("time-slider", "value"),
     State("vehicle-class-dropdown", "value"),
     State("day-dropdown", "value"),
     State("region-dropdown", "value"),
     State("map-type", "value")]
)
def update_dashboard(n_clicks, time_interval, start_date, end_date, time_range, 
                    vehicle_classes, days_of_week, regions, map_type):
    # Initialize with full dataset
    filtered_df = df.copy()
    
    # Apply filters if values are provided
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date) + timedelta(days=1)  # Include the end date
        filtered_df = filtered_df[(filtered_df['datetime'] >= start_date) & (filtered_df['datetime'] <= end_date)]
    
    if time_range:
        start_hour, end_hour = time_range
        filtered_df = filtered_df[(filtered_df['hour_of_day'] >= start_hour) & (filtered_df['hour_of_day'] <= end_hour)]
    
    if vehicle_classes:
        filtered_df = filtered_df[filtered_df['Vehicle Class'].isin(vehicle_classes)]
    
    if days_of_week:
        filtered_df = filtered_df[filtered_df['day_of_week'].isin(days_of_week)]
    
    if regions:
        filtered_df = filtered_df[filtered_df['Detection Region'].isin(regions)]
    
    # Create map with filtered data
    map_path = create_map(filtered_df, map_type)
    
    # Generate charts with filtered data
    time_chart = generate_time_series_chart(filtered_df, time_interval)
    vehicle_chart = generate_vehicle_class_chart(filtered_df)
    region_chart = generate_region_chart(filtered_df)
    
    # Generate insights
    insights = generate_insights(filtered_df)
    
    return map_path, time_chart, vehicle_chart, region_chart, insights

def generate_insights(filtered_df):
    """Generate data-driven insights based on the filtered data"""
    if filtered_df.empty:
        return html.P("No data available with the current filters. Please adjust your selection.")
    
    # Calculate key metrics
    total_entries = filtered_df['CRZ Entries'].sum()
    avg_entries_per_day = filtered_df.groupby(filtered_df['datetime'].dt.date)['CRZ Entries'].sum().mean()
    
    # Find peak hours and days
    hourly_data = filtered_df.groupby('hour_of_day')['CRZ Entries'].sum().reset_index()
    peak_hour = hourly_data.loc[hourly_data['CRZ Entries'].idxmax()]['hour_of_day']
    
    daily_data = filtered_df.groupby('day_of_week')['CRZ Entries'].sum().reset_index()
    peak_day = daily_data.loc[daily_data['CRZ Entries'].idxmax()]['day_of_week']
    
    # Find busiest entry point
    region_data = filtered_df.groupby('Detection Region')['CRZ Entries'].sum().reset_index()
    busiest_region = region_data.loc[region_data['CRZ Entries'].idxmax()]['Detection Region']
    
    # Find most common vehicle class
    vehicle_data = filtered_df.groupby('Vehicle Class')['CRZ Entries'].sum().reset_index()
    top_vehicle = vehicle_data.loc[vehicle_data['CRZ Entries'].idxmax()]['Vehicle Class']
    
    # Create insights components
    insights_components = [
        html.Div([
            html.H4("Key Metrics", className="text-primary mb-3"),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5(f"{int(total_entries):,}", className="display-5 text-center"),
                            html.P("Total Entries", className="text-muted text-center")
                        ], className="p-3 border rounded bg-light")
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.H5(f"{int(avg_entries_per_day):,}", className="display-5 text-center"),
                            html.P("Avg. Daily Entries", className="text-muted text-center")
                        ], className="p-3 border rounded bg-light")
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.H5(f"{len(filtered_df['Detection Region'].unique())}", className="display-5 text-center"),
                            html.P("Active Entry Points", className="text-muted text-center")
                        ], className="p-3 border rounded bg-light")
                    ], width=4)
                ], className="mb-4")
            ])
        ]),
        
        html.Div([
            html.H4("Traffic Patterns", className="text-primary mb-3"),
            html.Ul([
                html.Li(f"Peak traffic occurs at {int(peak_hour)}:00, with significant congestion lasting approximately 2-3 hours."),
                html.Li(f"{peak_day} is the busiest day of the week for Manhattan congestion."),
                html.Li(f"The busiest entry point is {busiest_region}."),
                html.Li(f"The most common vehicle type is {top_vehicle}.")
            ], className="list-unstyled")
        ], className="mb-4"),
        
        html.Div([
            html.H4("Recommendations", className="text-primary mb-3"),
            html.Ul([
                html.Li(f"Consider alternative routes during peak hours ({int(peak_hour)-1}:00 - {int(peak_hour)+1}:00)."),
                html.Li(f"If possible, plan travel outside of {peak_day}."),
                html.Li(f"The {busiest_region} area shows consistently high traffic and should be avoided during rush hours."),
                html.Li("Consider using public transportation during peak congestion periods.")
            ], className="list-unstyled")
        ])
    ]
    
    return insights_components

if __name__ == '__main__':
    app.run_server(debug=True) 