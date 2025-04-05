# Manhattan Congestion Analytics - Full-Stack Project Structure

```
manhattan-congestion-analytics/
│
├── app/                           # Main application directory
│   ├── __init__.py                # Flask application factory
│   ├── models/                    # Database models
│   │   ├── __init__.py
│   │   ├── user.py                # User model
│   │   └── congestion_data.py     # Data model
│   │
│   ├── api/                       # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication API
│   │   └── data.py                # Data API
│   │
│   ├── dashboards/                # Dash applications
│   │   ├── __init__.py
│   │   ├── main_dashboard.py      # Main analytics dashboard
│   │   └── insights_dashboard.py  # Insights dashboard
│   │
│   ├── static/                    # Static files
│   │   ├── css/                   # CSS files
│   │   ├── js/                    # JavaScript files
│   │   └── images/                # Image files
│   │
│   └── templates/                 # Jinja2 templates
│       ├── base.html              # Base template
│       ├── index.html             # Landing page
│       ├── auth/                  # Authentication templates
│       └── admin/                 # Admin templates
│
├── data/                          # Data processing scripts
│   ├── __init__.py
│   ├── etl.py                     # ETL pipeline
│   └── preprocessing.py           # Data preprocessing
│
├── migrations/                    # Database migrations
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_api.py                # API tests
│   ├── test_models.py             # Model tests
│   └── test_dashboards.py         # Dashboard tests
│
├── .env                           # Environment variables (not in git)
├── .gitignore                     # Git ignore file
├── config.py                      # Configuration settings
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Development dependencies
├── run.py                         # Application entry point
└── README.md                      # Project documentation
```

## Component Details

### Backend Components

1. **Database Models**
   - User model: Authentication and preferences
   - Congestion Data model: Processed and enriched MTA data

2. **API Endpoints**
   - Authentication: Registration, login, password reset
   - Data API: Endpoints for querying congestion data with filters

3. **ETL Pipeline**
   - Data import from CSV source
   - Processing and enrichment
   - Database storage
   - Scheduled updates

### Frontend Components

1. **Dash Dashboards**
   - Main analytics dashboard: Heatmap, charts, and filters
   - Insights dashboard: Automated analysis and recommendations

2. **Flask Templates**
   - Landing page
   - User profile and settings
   - Admin interface

### Infrastructure

1. **Authentication System**
   - JWT or session-based authentication
   - Role-based access control

2. **Database**
   - PostgreSQL for relational data
   - Redis for caching

3. **Deployment**
   - Docker containerization
   - Gunicorn/WSGI for production
   - Nginx for reverse proxy 