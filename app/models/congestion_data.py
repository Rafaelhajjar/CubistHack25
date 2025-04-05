from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db

class EntryPoint(db.Model):
    """Model for congestion zone entry points"""
    __tablename__ = 'entry_points'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    entries = db.relationship('CongestionEntry', backref='entry_point', lazy=True)
    
    def __repr__(self):
        return f'<EntryPoint {self.name}>'

class VehicleClass(db.Model):
    """Model for vehicle classifications"""
    __tablename__ = 'vehicle_classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Relationships
    entries = db.relationship('CongestionEntry', backref='vehicle_class', lazy=True)
    
    def __repr__(self):
        return f'<VehicleClass {self.name}>'

class CongestionEntry(db.Model):
    """Model for congestion zone entry data"""
    __tablename__ = 'congestion_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    entry_count = db.Column(db.Integer, nullable=False)
    excluded_count = db.Column(db.Integer, default=0)
    
    # Foreign keys
    entry_point_id = db.Column(db.Integer, db.ForeignKey('entry_points.id'), nullable=False)
    vehicle_class_id = db.Column(db.Integer, db.ForeignKey('vehicle_classes.id'), nullable=False)
    
    # Metadata
    time_period = db.Column(db.String(20))  # Morning, Afternoon, Evening, Overnight
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CongestionEntry {self.timestamp} - {self.entry_count}>'

class DailyAggregate(db.Model):
    """Precomputed daily aggregates for faster queries"""
    __tablename__ = 'daily_aggregates'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    entry_point_id = db.Column(db.Integer, db.ForeignKey('entry_points.id'), nullable=False)
    vehicle_class_id = db.Column(db.Integer, db.ForeignKey('vehicle_classes.id'), nullable=False)
    
    total_entries = db.Column(db.Integer, nullable=False)
    peak_hour = db.Column(db.Integer)  # Hour of day with highest entries
    peak_hour_count = db.Column(db.Integer)  # Entry count during peak hour
    
    # Relationships
    entry_point = db.relationship('EntryPoint')
    vehicle_class = db.relationship('VehicleClass')
    
    __table_args__ = (
        db.UniqueConstraint('date', 'entry_point_id', 'vehicle_class_id', name='_daily_unique'),
    )
    
    def __repr__(self):
        return f'<DailyAggregate {self.date} - {self.total_entries}>'

# Indices for query optimization
def create_indices():
    """Create database indices for performance optimization"""
    db.Index('idx_congestion_timestamp', CongestionEntry.timestamp)
    db.Index('idx_congestion_entry_point', CongestionEntry.entry_point_id)
    db.Index('idx_congestion_vehicle', CongestionEntry.vehicle_class_id)
    db.Index('idx_daily_date', DailyAggregate.date)
    db.Index('idx_combined_entry_search', 
             CongestionEntry.timestamp, 
             CongestionEntry.entry_point_id, 
             CongestionEntry.vehicle_class_id) 