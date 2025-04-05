import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Define the database connection
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define models
class EntryPoint(Base):
    """Model for congestion zone entry points"""
    __tablename__ = 'entry_points'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(Text)
    
    # Relationships
    entries = relationship('CongestionEntry', backref='entry_point', lazy=True)
    
    def __repr__(self):
        return f'<EntryPoint {self.name}>'

class VehicleClass(Base):
    """Model for vehicle classifications"""
    __tablename__ = 'vehicle_classes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    
    # Relationships
    entries = relationship('CongestionEntry', backref='vehicle_class', lazy=True)
    
    def __repr__(self):
        return f'<VehicleClass {self.name}>'

class CongestionEntry(Base):
    """Model for congestion zone entry data"""
    __tablename__ = 'congestion_entries'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    entry_count = Column(Integer, nullable=False)
    excluded_count = Column(Integer, default=0)
    
    # Foreign keys
    entry_point_id = Column(Integer, ForeignKey('entry_points.id'), nullable=False)
    vehicle_class_id = Column(Integer, ForeignKey('vehicle_classes.id'), nullable=False)
    
    # Metadata
    time_period = Column(String(20))  # Morning, Afternoon, Evening, Overnight
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CongestionEntry {self.timestamp} - {self.entry_count}>'

class DailyAggregate(Base):
    """Precomputed daily aggregates for faster queries"""
    __tablename__ = 'daily_aggregates'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    entry_point_id = Column(Integer, ForeignKey('entry_points.id'), nullable=False)
    vehicle_class_id = Column(Integer, ForeignKey('vehicle_classes.id'), nullable=False)
    
    total_entries = Column(Integer, nullable=False)
    peak_hour = Column(Integer)  # Hour of day with highest entries
    peak_hour_count = Column(Integer)  # Entry count during peak hour
    
    # Relationships
    entry_point = relationship('EntryPoint')
    vehicle_class = relationship('VehicleClass')
    
    def __repr__(self):
        return f'<DailyAggregate {self.date} - {self.total_entries}>'

# Create all tables
def init_db():
    """Initialize the database"""
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 