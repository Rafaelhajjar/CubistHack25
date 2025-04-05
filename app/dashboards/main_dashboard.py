import os
import datetime
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from folium.plugins import HeatMapWithTime, MarkerCluster
import tempfile
import numpy as np
from flask import current_app
import requests

# Dashboard init function
def init_dashboard(server):
    """Initialize and attach the Dash app to the Flask server"""
    # Create Dash app
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix=current_app.config.get('DASH_ROUTES_PATHNAME_PREFIX', '/dash/'),
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title='Manhattan Congestion Analytics'
    )
    
    # Set up the layout
    init_dashboard_layout(dash_app)
    
    # Set up callbacks
    init_callbacks(dash_app)
    
    return dash_app.server

def init_dashboard_layout(dash_app):
    """Initialize the Dash app layout"""
    # Get data ranges for filters from API
    try:
        # In a real app, we'd get these from the API
        # For now, use defaults
        date_min = datetime.date(2025, 3, 29)
        date_max = datetime.date(2025, 4, 30)
        vehicle_classes = ["1 - Cars, Pickups and Vans", "TLC Taxi/FHV", "2 - All Trucks and Buses"]
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        regions = ["Brooklyn", "Queens", "Lincoln Tunnel", "Holland Tunnel", "Manhattan Bridge"]
    except Exception as e:
        # Use fallbacks
        date_min = datetime.date(2025, 1, 1)
        date_max = datetime.date(2025, 12, 31)
        vehicle_classes = []
        days_of_week = []
        regions = []
    
    # Define the layout
    dash_app.layout = dbc.Container([
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
                    min_date_allowed=date_min,
                    max_date_allowed=date_max,
                    start_date=date_min,
                    end_date=min(date_min + datetime.timedelta(days=7), date_max),
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
                    options=[{'label': cls, 'value': cls} for cls in vehicle_classes],
                    multi=True,
                    placeholder="Select vehicle class(es)",
                    className="mb-3"
                ),
                
                html.Label("Day of Week:"),
                dcc.Dropdown(
                    id='day-dropdown',
                    options=[{'label': day, 'value': day} for day in days_of_week],
                    multi=True,
                    placeholder="Select day(s) of week",
                    className="mb-3"
                ),
                
                html.Label("Detection Region:"),
                dcc.Dropdown(
                    id='region-dropdown',
                    options=[{'label': region, 'value': region} for region in regions],
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
                
                dbc.Button("Apply Filters", id="apply-button", color="primary", className="w-100 mb-4"),
                
                # Save dashboard configuration
                html.Hr(),
                html.Label("Save Dashboard:"),
                dbc.Input(id="dashboard-name", placeholder="Dashboard name", className="mb-2"),
                dbc.Button("Save Current View", id="save-button", color="secondary", className="w-100"),
                html.Div(id="save-status", className="mt-2 text-center")
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
        dcc.Store(id='filtered-data'),
        dcc.Store(id='dashboard-config'),
        
        # Interval for data refresh
        dcc.Interval(
            id='interval-component',
            interval=5*60*1000,  # in milliseconds (5 minutes)
            n_intervals=0
        )
    ], fluid=True, className="p-4")

def init_callbacks(dash_app):
    """Initialize Dash callbacks"""
    
    @dash_app.callback(
        Output('filtered-data', 'data'),
        [Input('apply-button', 'n_clicks'),
         Input('interval-component', 'n_intervals')],
        [State('date-picker', 'start_date'),
         State('date-picker', 'end_date'),
         State('time-slider', 'value'),
         State('vehicle-class-dropdown', 'value'),
         State('day-dropdown', 'value'),
         State('region-dropdown', 'value'),
         State('filtered-data', 'data')]
    )
    def fetch_filtered_data(n_clicks, n_intervals, start_date, end_date, time_range, 
                           vehicle_classes, days_of_week, regions, current_data):
        """Fetch data from API based on filters"""
        # In a real app, we would call the API here
        # For the hackathon demo, we'll simulate API results
        
        # Return a placeholder response
        # In a real implementation, this would fetch from the API
        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'time_range': time_range,
                'vehicle_classes': vehicle_classes,
                'days_of_week': days_of_week,
                'regions': regions
            },
            'data_summary': {
                'total_entries': 1256789,
                'peak_hour': 8,
                'peak_hour_count': 125678,
                'peak_day': 'Monday',
                'busiest_region': 'Lincoln Tunnel',
                'top_vehicle': '1 - Cars, Pickups and Vans'
            }
        }
    
    @dash_app.callback(
        [Output('map-iframe', 'src'),
         Output('time-series-chart', 'figure'),
         Output('vehicle-class-chart', 'figure'),
         Output('region-chart', 'figure'),
         Output('insights-container', 'children')],
        [Input('filtered-data', 'data'),
         Input('time-interval', 'value'),
         Input('map-type', 'value')]
    )
    def update_dashboard(data, time_interval, map_type):
        """Update all dashboard components based on filtered data"""
        # This would use the actual filtered data in a real implementation
        # For the hackathon, we'll use placeholder visualizations
        
        # Create map
        map_path = create_placeholder_map(map_type)
        
        # Create charts
        time_chart = create_placeholder_time_chart(time_interval)
        vehicle_chart = create_placeholder_vehicle_chart()
        region_chart = create_placeholder_region_chart()
        
        # Create insights
        insights = create_placeholder_insights(data)
        
        return map_path, time_chart, vehicle_chart, region_chart, insights
    
    @dash_app.callback(
        Output('save-status', 'children'),
        [Input('save-button', 'n_clicks')],
        [State('dashboard-name', 'value'),
         State('filtered-data', 'data')]
    )
    def save_dashboard_config(n_clicks, dashboard_name, data):
        """Save the current dashboard configuration"""
        if not n_clicks:
            return ""
        
        if not dashboard_name:
            return html.Span("Please provide a dashboard name", className="text-danger")
        
        # In a real app, this would save to the database
        return html.Span(f"Dashboard '{dashboard_name}' saved successfully!", className="text-success")

# Helper functions for dashboard components
def create_placeholder_map(map_type):
    """Create a folium map for visualization"""
    # Create base map centered around Manhattan
    map_center = [40.7831, -73.9712]
    m = folium.Map(location=map_center, zoom_start=12, tiles='CartoDB positron')
    
    # Add a placeholder tile layer to show this is a demo
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='Demo Mode - Simulated Data',
        name='Demo Layer',
        overlay=True,
        control=True
    ).add_to(m)
    
    # Save to temporary file
    _, temp_path = tempfile.mkstemp(suffix='.html')
    m.save(temp_path)
    
    return temp_path

def create_placeholder_time_chart(interval='day'):
    """Create a time series chart"""
    # Create dummy data
    if interval == 'day':
        dates = pd.date_range(start='2025-03-29', end='2025-04-05')
        values = [45000, 87000, 76000, 91000, 68000, 58000, 73000, 42000]
        df = pd.DataFrame({'date': dates, 'entries': values})
        
        fig = px.line(
            df, 
            x='date', 
            y='entries', 
            title='Daily Congestion Entries',
            labels={'date': 'Date', 'entries': 'Total Entries'}
        )
    else:
        hours = list(range(24))
        values = [2100, 1500, 900, 600, 800, 1700, 4500, 7800, 9200, 8500, 
                 7600, 8100, 8700, 8200, 7900, 8300, 9100, 8700, 7300, 6500, 5200, 4100, 3600, 2700]
        df = pd.DataFrame({'hour': hours, 'entries': values})
        
        fig = px.line(
            df, 
            x='hour', 
            y='entries', 
            title='Hourly Congestion Entries',
            labels={'hour': 'Hour of Day', 'entries': 'Total Entries'}
        )
    
    # Customize layout
    fig.update_layout(
        template='plotly_white',
        xaxis_title='Time',
        yaxis_title='Total Entries',
        hovermode='x unified'
    )
    
    return fig

def create_placeholder_vehicle_chart():
    """Create a bar chart for vehicle classes"""
    vehicles = ["1 - Cars, Pickups and Vans", "TLC Taxi/FHV", "2 - All Trucks and Buses", 
               "3 - Misc. Vehicles", "4 - Motorcycles"]
    values = [320000, 180000, 95000, 28000, 12000]
    df = pd.DataFrame({'vehicle': vehicles, 'entries': values})
    
    fig = px.bar(
        df, 
        x='vehicle', 
        y='entries', 
        title='Entries by Vehicle Class',
        color='entries',
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

def create_placeholder_region_chart():
    """Create a bar chart for entry regions"""
    regions = ["Lincoln Tunnel", "Queens", "Brooklyn", "Holland Tunnel", 
              "Manhattan Bridge", "Brooklyn Bridge", "Williamsburg Bridge"]
    values = [162000, 143000, 125000, 98000, 87000, 81000, 63000]
    df = pd.DataFrame({'region': regions, 'entries': values})
    
    fig = px.bar(
        df, 
        x='region', 
        y='entries', 
        title='Entries by Detection Region',
        color='entries',
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

def create_placeholder_insights(data):
    """Generate insights components"""
    if not data or 'data_summary' not in data:
        return html.P("No data available. Please apply filters to see insights.")
    
    # Use data from the mock API response
    summary = data['data_summary']
    
    insights_components = [
        html.Div([
            html.H4("Key Metrics", className="text-primary mb-3"),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5(f"{summary['total_entries']:,}", className="display-5 text-center"),
                            html.P("Total Entries", className="text-muted text-center")
                        ], className="p-3 border rounded bg-light")
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.H5(f"{summary['total_entries'] // 7:,}", className="display-5 text-center"),
                            html.P("Avg. Daily Entries", className="text-muted text-center")
                        ], className="p-3 border rounded bg-light")
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.H5("8", className="display-5 text-center"),
                            html.P("Active Entry Points", className="text-muted text-center")
                        ], className="p-3 border rounded bg-light")
                    ], width=4)
                ], className="mb-4")
            ])
        ]),
        
        html.Div([
            html.H4("Traffic Patterns", className="text-primary mb-3"),
            html.Ul([
                html.Li(f"Peak traffic occurs at {summary['peak_hour']}:00, with significant congestion lasting approximately 2-3 hours."),
                html.Li(f"{summary['peak_day']} is the busiest day of the week for Manhattan congestion."),
                html.Li(f"The busiest entry point is {summary['busiest_region']}."),
                html.Li(f"The most common vehicle type is {summary['top_vehicle']}.")
            ], className="list-unstyled")
        ], className="mb-4"),
        
        html.Div([
            html.H4("Recommendations", className="text-primary mb-3"),
            html.Ul([
                html.Li(f"Consider alternative routes during peak hours ({summary['peak_hour']-1}:00 - {summary['peak_hour']+1}:00)."),
                html.Li(f"If possible, plan travel outside of {summary['peak_day']}."),
                html.Li(f"The {summary['busiest_region']} area shows consistently high traffic and should be avoided during rush hours."),
                html.Li("Consider using public transportation during peak congestion periods.")
            ], className="list-unstyled")
        ])
    ]
    
    return insights_components 