from flask import jsonify, request, url_for, g, abort
from app import db
from app.api import bp
from app.models.congestion_data import CongestionEntry, EntryPoint, VehicleClass, DailyAggregate
# If token_auth is needed but not available, we can comment it out for now
# from app.api.auth import token_auth
from datetime import datetime, timedelta
import pandas as pd

@bp.route('/congestion/entry-points', methods=['GET'])
def get_entry_points():
    """Get all entry points"""
    entry_points = EntryPoint.query.all()
    return jsonify({
        'entry_points': [
            {
                'id': ep.id,
                'name': ep.name,
                'latitude': ep.latitude,
                'longitude': ep.longitude,
                'description': ep.description
            } for ep in entry_points
        ]
    })

@bp.route('/congestion/vehicle-classes', methods=['GET'])
def get_vehicle_classes():
    """Get all vehicle classes"""
    vehicle_classes = VehicleClass.query.all()
    return jsonify({
        'vehicle_classes': [
            {
                'id': vc.id,
                'name': vc.name,
                'description': vc.description
            } for vc in vehicle_classes
        ]
    })


@bp.route('/congestion/entries', methods=['GET'])
def get_congestion_entries():
    """
    Get congestion entries with filtering
    
    Query parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - start_hour: Starting hour (0-23)
    - end_hour: Ending hour (0-23)
    - entry_points: Comma-separated list of entry point IDs
    - vehicle_classes: Comma-separated list of vehicle class IDs
    - time_period: Morning, Afternoon, Evening, Overnight
    - limit: Maximum number of results (default 1000)
    - page: Page number (default 1)
    """
    # Parse query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_hour = request.args.get('start_hour', type=int)
    end_hour = request.args.get('end_hour', type=int)
    entry_points = request.args.get('entry_points')
    vehicle_classes = request.args.get('vehicle_classes')
    time_period = request.args.get('time_period')
    limit = min(int(request.args.get('limit', 1000)), 10000)  # Cap at 10,000
    page = int(request.args.get('page', 1))
    
    # Build the query
    query = CongestionEntry.query
    
    # Apply filters
    if start_date:
        query = query.filter(CongestionEntry.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(CongestionEntry.timestamp <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
    if start_hour is not None:
        query = query.filter(db.extract('hour', CongestionEntry.timestamp) >= start_hour)
    if end_hour is not None:
        query = query.filter(db.extract('hour', CongestionEntry.timestamp) <= end_hour)
    if entry_points:
        entry_point_ids = [int(ep_id) for ep_id in entry_points.split(',')]
        query = query.filter(CongestionEntry.entry_point_id.in_(entry_point_ids))
    if vehicle_classes:
        vehicle_class_ids = [int(vc_id) for vc_id in vehicle_classes.split(',')]
        query = query.filter(CongestionEntry.vehicle_class_id.in_(vehicle_class_ids))
    if time_period:
        query = query.filter(CongestionEntry.time_period == time_period)
    
    # Execute paginated query
    paginated_results = query.order_by(CongestionEntry.timestamp).paginate(page=page, per_page=limit, error_out=False)
    
    # Format results
    return jsonify({
        'entries': [
            {
                'id': entry.id,
                'timestamp': entry.timestamp.isoformat(),
                'entry_point_id': entry.entry_point_id,
                'entry_point_name': entry.entry_point.name,
                'vehicle_class_id': entry.vehicle_class_id,
                'vehicle_class_name': entry.vehicle_class.name,
                'entry_count': entry.entry_count,
                'excluded_count': entry.excluded_count,
                'time_period': entry.time_period
            } for entry in paginated_results.items
        ],
        'total': paginated_results.total,
        'pages': paginated_results.pages,
        'page': page
    })

@bp.route('/congestion/aggregates/daily', methods=['GET'])
def get_daily_aggregates():
    """
    Get daily aggregated congestion data
    
    Query parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - entry_points: Comma-separated list of entry point IDs
    - vehicle_classes: Comma-separated list of vehicle class IDs
    """
    # Parse query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    entry_points = request.args.get('entry_points')
    vehicle_classes = request.args.get('vehicle_classes')
    
    # Build the query
    query = DailyAggregate.query
    
    # Apply filters
    if start_date:
        query = query.filter(DailyAggregate.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(DailyAggregate.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if entry_points:
        entry_point_ids = [int(ep_id) for ep_id in entry_points.split(',')]
        query = query.filter(DailyAggregate.entry_point_id.in_(entry_point_ids))
    if vehicle_classes:
        vehicle_class_ids = [int(vc_id) for vc_id in vehicle_classes.split(',')]
        query = query.filter(DailyAggregate.vehicle_class_id.in_(vehicle_class_ids))
    
    # Execute query
    results = query.order_by(DailyAggregate.date).all()
    
    # Format results
    return jsonify({
        'daily_aggregates': [
            {
                'date': agg.date.isoformat(),
                'entry_point_id': agg.entry_point_id,
                'entry_point_name': agg.entry_point.name,
                'vehicle_class_id': agg.vehicle_class_id,
                'vehicle_class_name': agg.vehicle_class.name,
                'total_entries': agg.total_entries,
                'peak_hour': agg.peak_hour,
                'peak_hour_count': agg.peak_hour_count
            } for agg in results
        ]
    })

@bp.route('/congestion/heatmap-data', methods=['GET'])
def get_heatmap_data():
    """
    Get data formatted for heatmap visualization
    
    Query parameters:
    - date: Specific date (YYYY-MM-DD), defaults to most recent
    - interval: Time interval ('hour', '30min', '15min'), defaults to 'hour'
    """
    date_str = request.args.get('date')
    interval = request.args.get('interval', 'hour')
    
    # Determine date to use
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        # Get the most recent date in the database
        latest_entry = CongestionEntry.query.order_by(CongestionEntry.timestamp.desc()).first()
        if not latest_entry:
            return jsonify({'error': 'No data available'}), 404
        target_date = latest_entry.timestamp.date()
    
    # Query data for the target date
    entries = CongestionEntry.query.filter(
        db.func.date(CongestionEntry.timestamp) == target_date
    ).order_by(CongestionEntry.timestamp).all()
    
    if not entries:
        return jsonify({'error': f'No data available for {target_date}'}), 404
    
    # Load into pandas for resampling
    df = pd.DataFrame([
        {
            'timestamp': entry.timestamp,
            'latitude': entry.entry_point.latitude,
            'longitude': entry.entry_point.longitude,
            'entry_count': entry.entry_count
        }
        for entry in entries
    ])
    
    # Group by interval and location
    df['interval'] = df['timestamp'].dt.floor(interval)
    heatmap_data = df.groupby(['interval', 'latitude', 'longitude'])['entry_count'].sum().reset_index()
    
    # Format for HeatMapWithTime
    intervals = sorted(heatmap_data['interval'].unique())
    formatted_data = []
    
    for interval_time in intervals:
        interval_df = heatmap_data[heatmap_data['interval'] == interval_time]
        data_points = interval_df[['latitude', 'longitude', 'entry_count']].values.tolist()
        formatted_data.append(data_points)
    
    return jsonify({
        'data': formatted_data,
        'intervals': [interval.isoformat() for interval in intervals],
        'date': target_date.isoformat()
    }) 