# Manhattan Congestion Analytics Dashboard

An interactive full-stack web application for analyzing and visualizing traffic congestion patterns in Manhattan's Congestion Relief Zone based on MTA data.

## Features

- **Interactive Heatmap Visualization**: View congestion patterns over time with a dynamic heatmap
- **Advanced Filtering Capabilities**: Filter data by date, time, vehicle class, day of week, and entry point
- **Multiple Visualization Types**: Toggle between heatmap and marker-based visualizations
- **Comprehensive Analytics**: View time series trends, vehicle class distribution, and entry point statistics
- **Data-Driven Insights**: Get automatically generated insights and recommendations based on filtered data
- **User Authentication**: Secure login system for personalized dashboards
- **Dashboard Saving**: Save and reload your favorite dashboard configurations
- **REST API**: Full API access to congestion data and analytics
- **Database Backend**: Optimized SQL database for efficient querying

## Full-Stack Architecture

This application follows a modern full-stack architecture:

### Backend Components
- **Flask API**: RESTful API endpoints for data access
- **SQLAlchemy ORM**: Database models and queries
- **PostgreSQL Database**: Production-ready database for data storage
- **ETL Pipeline**: Data ingestion and processing system
- **Authentication System**: JWT token-based authentication

### Frontend Components
- **Dash Framework**: Interactive dashboards and visualizations
- **Plotly**: Dynamic charts and graphs
- **Folium/Leaflet**: Geographic data visualizations
- **Flask Templates**: Server-side rendering for non-dashboard pages
- **Bootstrap**: Responsive UI styling

## Setup Instructions

1. Clone this repository:
```bash
git clone <repository-url>
cd manhattan-congestion-analytics
```

2. Set up a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create a .env file):
```
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URI=sqlite:///app.db  # For local development
```

5. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Import data (local development):
```bash
python -m data.etl
```

7. Run the application:
```bash
flask run
```

8. Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

## API Documentation

The application provides a comprehensive API:

- `GET /api/congestion/entry-points` - Get all entry points
- `GET /api/congestion/vehicle-classes` - Get all vehicle classes
- `GET /api/congestion/entries` - Get congestion entries with filtering
- `GET /api/congestion/aggregates/daily` - Get daily aggregated congestion data
- `GET /api/congestion/heatmap-data` - Get data formatted for heatmap visualization
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/tokens` - Get authentication token
- `DELETE /api/auth/tokens` - Revoke the current token
- `GET /api/auth/profile` - Get the current user's profile

## Project Structure

```
manhattan-congestion-analytics/
│
├── app/                           # Main application directory
│   ├── models/                    # Database models
│   ├── api/                       # API endpoints
│   ├── dashboards/                # Dash applications
│   ├── static/                    # Static files
│   └── templates/                 # Jinja2 templates
│
├── data/                          # Data processing scripts
├── migrations/                    # Database migrations
├── tests/                         # Test suite
├── config.py                      # Configuration settings
├── requirements.txt               # Python dependencies
├── run.py                         # Application entry point
└── README.md                      # Project documentation
```

## Data Source

This application uses the MTA Congestion Relief Zone Vehicle Entries dataset, which provides detailed information about vehicle entries into Manhattan's congestion zone.

## Dashboard Tabs

1. **Map View**: Interactive map visualization with heatmap or marker options
2. **Analytics**: Charts and graphs showing temporal patterns and distribution statistics
3. **Insights**: Automated analysis providing key metrics, traffic patterns, and recommendations

## Deployment

For production deployment:

1. Set up a PostgreSQL database
2. Configure environment variables for production
3. Use Gunicorn as the WSGI server
4. Set up Nginx as a reverse proxy
5. Use Docker for containerization (optional)

## Technologies Used

- **Python**: Flask, SQLAlchemy, Pandas, NumPy
- **Dash/Plotly**: Interactive visualizations
- **Folium/Leaflet**: Map visualizations
- **PostgreSQL**: Database
- **Bootstrap**: Frontend styling
- **JavaScript**: Client-side enhancements

