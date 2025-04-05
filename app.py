import os
import random
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, HeatMapWithTime, MarkerCluster
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

###############################################################################
# 1) A function that builds a basic heatmap with random intensities
###############################################################################
def build_basic_heatmap_html():
    """
    Create a simple Folium heatmap using random intensities at known NYC locations.
    Return the HTML for embedding in an iframe or other container.
    """
    # Dictionary of NYC entry points (some repeats removed)
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
        "FDR Drive at 34th St": (40.7448, -73.9721),
    }

    # Create a Folium map centered near Manhattan
    m = folium.Map(location=[40.7580, -73.9855], zoom_start=12, tiles='CartoDB positron')

    # Build [lat, lon, intensity] with random values for demonstration
    heat_data = []
    for name, (lat, lon) in entry_points.items():
        intensity = random.randint(50, 200)  # random for demo
        heat_data.append([lat, lon, intensity])

    # Add the heat layer
    HeatMap(heat_data, radius=40, min_opacity=0.2, max_opacity=0.7).add_to(m)

    # Return entire <div> + <script> for embedding
    return m._repr_html_()

###############################################################################
# 2) Load and process data (unchanged)
###############################################################################
def load_and_process_data():
    try:
        csv_file_path = 'MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv'
        df = pd.read_csv(csv_file_path)
        print("CSV file loaded successfully.")

        # --- Data Preprocessing ---
        df['datetime'] = pd.to_datetime(df['Toll 10 Minute Block'], errors='coerce')
        df.dropna(subset=['datetime'], inplace=True)

        df['CRZ Entries'] = pd.to_numeric(df['CRZ Entries'], errors='coerce')
        df.dropna(subset=['CRZ Entries'], inplace=True)
        df['CRZ Entries'] = df['CRZ Entries'].astype(int)

        df['day_of_week'] = df['datetime'].dt.day_name()
        df['hour_of_day'] = df['datetime'].dt.hour
        df['date'] = df['datetime'].dt.date

        # Map coordinates
        extended_entry_points = {
            "Brooklyn": (40.7061, -73.9969),
            "Queens": (40.7570, -73.9543),
            "Queens Midtown Tunnel": (40.7440, -73.9713),
            "West Side Highway": (40.7713, -73.9916),
            "West 60th St": (40.7690, -73.9851),
            "Manhattan Bridge": (40.7075, -73.9903),
            "Lincoln Tunnel": (40.7608, -74.0021),
            "Holland Tunnel": (40.7256, -74.0119),
            "FDR Drive": (40.7625, -73.9595),
            "East 60th St": (40.7625, -73.9595),
            "New Jersey": (40.7608, -74.0021),
            "Brooklyn Battery Tunnel": (40.7001, -74.0145),
            "Battery Tunnel": (40.7001, -74.0145),
            "Hugh L. Carey Tunnel": (40.7001, -74.0145),
            "Williamsburg Bridge": (40.7131, -73.9722),
            "Brooklyn Bridge": (40.7061, -73.9969),
            "Manhattan": (40.7075, -73.9903),
            "Queensboro Bridge": (40.7570, -73.9543),
            "Queens Tunnel": (40.7440, -73.9713),
            "Midtown Tunnel": (40.7440, -73.9713),
            "Holland": (40.7256, -74.0119),
            "Brooklyn Tunnel": (40.7001, -74.0145),
            "Williamsburg": (40.7131, -73.9722),
        }

        clean_entry_points = {key.strip(): coords for key, coords in extended_entry_points.items()}
        lat_map = {name: coords[0] for name, coords in clean_entry_points.items()}
        lon_map = {name: coords[1] for name, coords in clean_entry_points.items()}

        df['Detection Region'] = df['Detection Region'].str.strip()
        df['latitude'] = df['Detection Region'].map(lat_map)
        df['longitude'] = df['Detection Region'].map(lon_map)

        df.dropna(subset=['latitude', 'longitude'], inplace=True)

        return df
    except Exception as e:
        print(f"Error processing data: {e}")
        return pd.DataFrame()  # Return empty dataframe on error

df = load_and_process_data()
print(f"Loaded data shape: {df.shape}")

###############################################################################
# 3) Define your analytics & map-making functions (unchanged)
###############################################################################
def get_hourly_totals(dataframe):
    return dataframe.groupby('hour_of_day')['CRZ Entries'].sum().reset_index()

def get_daily_totals(dataframe):
    return dataframe.groupby('day_of_week')['CRZ Entries'].sum().reset_index()

def get_region_totals(dataframe):
    return dataframe.groupby('Detection Region')['CRZ Entries'].sum().reset_index()

def get_vehicle_class_totals(dataframe):
    return dataframe.groupby('Vehicle Class')['CRZ Entries'].sum().reset_index()

def get_time_period_totals(dataframe):
    return dataframe.groupby('Time Period')['CRZ Entries'].sum().reset_index()

def generate_heatmap_data(filtered_df):
    df_heatmap = filtered_df[['datetime', 'latitude', 'longitude', 'CRZ Entries']].copy()
    df_heatmap.dropna(inplace=True)
    df_heatmap['hour'] = df_heatmap['datetime'].dt.floor('H')
    heatmap_data = df_heatmap.groupby(['hour', 'latitude', 'longitude'])['CRZ Entries'].sum().reset_index()

    time_index = sorted(heatmap_data['hour'].unique())
    data_for_heatmap = []
    for hour in time_index:
        hourly_data = heatmap_data[heatmap_data['hour'] == hour][['latitude', 'longitude', 'CRZ Entries']].values.tolist()
        data_for_heatmap.append(hourly_data)

    return data_for_heatmap, [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in time_index]

def create_map(filtered_df, map_type='heatmap'):
    map_center = [40.7831, -73.9712]
    m = folium.Map(location=map_center, zoom_start=12, tiles='CartoDB positron')
    
    if map_type == 'heatmap':
        heatmap_data, time_index = generate_heatmap_data(filtered_df)
        if heatmap_data:
            heatmap_wt = HeatMapWithTime(
                data=heatmap_data,
                index=time_index,
                gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'},
                min_opacity=0.1,
                max_opacity=0.7,
                radius=100,
                use_local_extrema=True,
                auto_play=True,
                display_index=True
            )
            m.add_child(heatmap_wt)

    elif map_type == 'markers':
        marker_data = filtered_df.groupby(['Detection Region', 'latitude', 'longitude'])['CRZ Entries'].sum().reset_index()
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in marker_data.iterrows():
            radius = min(25, max(5, np.log1p(row['CRZ Entries']) * 3))
            popup_content = f"""
            <div style="width: 200px">
                <h4>{row['Detection Region']}</h4>
                <p><b>Total Entries:</b> {int(row['CRZ Entries'])}</p>
            </div>
            """
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=radius,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(marker_cluster)
    
    # Instead of saving to a file, return the HTML string directly.
    return m._repr_html_()

###############################################################################
# 4) Create the Dash Layout
###############################################################################
import plotly.express as px
import plotly.graph_objects as go

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
                        # Use srcDoc to embed the HTML directly
                        children=[
                            html.Iframe(
                                id="map-iframe",
                                srcDoc=build_basic_heatmap_html(),  # static heatmap on load
                                style={"border": "none", "width": "100%", "height": "100%"}
                            )
                        ]
                    )
                ], label="Map View", tab_id="map-tab"),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([dcc.Graph(id="time-series-chart")], width=12, className="mb-4"),
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
                        
                        dbc.Col([dcc.Graph(id="vehicle-class-chart")], width=6),
                        dbc.Col([dcc.Graph(id="region-chart")], width=6)
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
    
    dcc.Store(id='filtered-data')
], fluid=True)

###############################################################################
# 5) Callbacks & Insights (unchanged)
###############################################################################
@app.callback(
    [
        # Change output property to "srcDoc" for embedding raw HTML
        Output("map-iframe", "srcDoc"),
        Output("time-series-chart", "figure"),
        Output("vehicle-class-chart", "figure"),
        Output("region-chart", "figure"),
        Output("insights-container", "children")
    ],
    [
        Input("apply-button", "n_clicks"),
        Input("time-interval", "value")
    ],
    [
        State("date-picker", "start_date"),
        State("date-picker", "end_date"),
        State("time-slider", "value"),
        State("vehicle-class-dropdown", "value"),
        State("day-dropdown", "value"),
        State("region-dropdown", "value"),
        State("map-type", "value")
    ]
)
def update_dashboard(n_clicks, time_interval, start_date, end_date, time_range, 
                    vehicle_classes, days_of_week, regions, map_type):
    filtered_df = df.copy()
    
    # Filter if inputs provided
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date) + timedelta(days=1)
        filtered_df = filtered_df[(filtered_df['datetime'] >= start_date) & (filtered_df['datetime'] < end_date)]
    
    if time_range:
        start_hour, end_hour = time_range
        filtered_df = filtered_df[(filtered_df['hour_of_day'] >= start_hour) & (filtered_df['hour_of_day'] <= end_hour)]
    
    if vehicle_classes:
        filtered_df = filtered_df[filtered_df['Vehicle Class'].isin(vehicle_classes)]
    
    if days_of_week:
        filtered_df = filtered_df[filtered_df['day_of_week'].isin(days_of_week)]
    
    if regions:
        filtered_df = filtered_df[filtered_df['Detection Region'].isin(regions)]
    
    # Create new Folium map & get its HTML string
    map_html = create_map(filtered_df, map_type)
    
    # Generate charts with filtered data
    time_chart = generate_time_series_chart(filtered_df, time_interval)
    vehicle_chart = generate_vehicle_class_chart(filtered_df)
    region_chart = generate_region_chart(filtered_df)
    insights = generate_insights(filtered_df)
    
    # Return the HTML string for the map in srcDoc, plus charts & insights
    return map_html, time_chart, vehicle_chart, region_chart, insights

def generate_insights(filtered_df):
    if filtered_df.empty:
        return html.P("No data available with the current filters. Please adjust your selection.")
    
    total_entries = filtered_df['CRZ Entries'].sum()
    avg_entries_per_day = filtered_df.groupby(filtered_df['datetime'].dt.date)['CRZ Entries'].sum().mean()
    
    hourly_data = filtered_df.groupby('hour_of_day')['CRZ Entries'].sum().reset_index()
    peak_hour = hourly_data.loc[hourly_data['CRZ Entries'].idxmax()]['hour_of_day']
    
    daily_data = filtered_df.groupby('day_of_week')['CRZ Entries'].sum().reset_index()
    peak_day = daily_data.loc[daily_data['CRZ Entries'].idxmax()]['day_of_week']
    
    region_data = filtered_df.groupby('Detection Region')['CRZ Entries'].sum().reset_index()
    busiest_region = region_data.loc[region_data['CRZ Entries'].idxmax()]['Detection Region']
    
    vehicle_data = filtered_df.groupby('Vehicle Class')['CRZ Entries'].sum().reset_index()
    top_vehicle = vehicle_data.loc[vehicle_data['CRZ Entries'].idxmax()]['Vehicle Class']
    
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

###############################################################################
# 6) Run the Server
###############################################################################
if __name__ == '__main__':
    app.run_server(debug=True)
