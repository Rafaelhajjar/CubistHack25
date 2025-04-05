import os
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Entry Point mapping - same as in the original app
entry_points = {
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
    "Williamsburg": (40.7131, -73.9722)
}

def connect_to_database():
    """Create database connection from environment variables"""
    db_uri = os.environ.get('DATABASE_URI', 'sqlite:///congestion_data.db')
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine)
    return engine, Session()

def load_csv_data(file_path):
    """Load data from CSV file"""
    logger.info(f"Loading data from {file_path}")
    try:
        # Read the CSV in chunks to handle large files
        chunks = pd.read_csv(file_path, chunksize=100000)
        return pd.concat(chunks)
    except Exception as e:
        logger.error(f"Error loading CSV data: {e}")
        raise

def preprocess_data(df):
    """Clean and preprocess the data"""
    logger.info("Preprocessing data...")
    
    # Convert to datetime
    df['datetime'] = pd.to_datetime(df['Toll 10 Minute Block'], errors='coerce')
    df.dropna(subset=['datetime'], inplace=True)
    
    # Extract date components
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.day_name()
    
    # Convert 'CRZ Entries' to numeric
    df['CRZ Entries'] = pd.to_numeric(df['CRZ Entries'], errors='coerce')
    df.dropna(subset=['CRZ Entries'], inplace=True)
    df['CRZ Entries'] = df['CRZ Entries'].astype(int)
    
    # Convert 'Excluded Roadway Entries' to numeric
    df['Excluded Roadway Entries'] = pd.to_numeric(df['Excluded Roadway Entries'], errors='coerce')
    df.fillna({'Excluded Roadway Entries': 0}, inplace=True)
    df['Excluded Roadway Entries'] = df['Excluded Roadway Entries'].astype(int)
    
    # Clean region names
    df['Detection Region'] = df['Detection Region'].str.strip()
    
    logger.info(f"Preprocessed data shape: {df.shape}")
    return df

def populate_entry_points(engine, session):
    """Populate entry points table"""
    logger.info("Populating entry points table...")
    
    # Check if table is already populated
    result = session.execute(text("SELECT COUNT(*) FROM entry_points"))
    count = result.scalar()
    
    if count > 0:
        logger.info(f"Entry points table already has {count} records. Skipping.")
        return
    
    # Prepare data for bulk insert
    entry_point_data = []
    for name, (lat, lon) in entry_points.items():
        entry_point_data.append({
            'name': name,
            'latitude': lat,
            'longitude': lon,
            'description': f"Entry point at {name}"
        })
    
    # Insert data
    entry_points_df = pd.DataFrame(entry_point_data)
    entry_points_df.to_sql('entry_points', engine, if_exists='append', index=False)
    session.commit()
    
    logger.info(f"Added {len(entry_point_data)} entry points")

def populate_vehicle_classes(engine, session, df):
    """Populate vehicle classes table"""
    logger.info("Populating vehicle classes table...")
    
    # Check if table is already populated
    result = session.execute(text("SELECT COUNT(*) FROM vehicle_classes"))
    count = result.scalar()
    
    if count > 0:
        logger.info(f"Vehicle classes table already has {count} records. Skipping.")
        return
    
    # Get unique vehicle classes from data
    unique_classes = df['Vehicle Class'].unique()
    
    # Prepare data for bulk insert
    vehicle_class_data = []
    for vc in unique_classes:
        vehicle_class_data.append({
            'name': vc,
            'description': f"Vehicle class: {vc}"
        })
    
    # Insert data
    vehicle_classes_df = pd.DataFrame(vehicle_class_data)
    vehicle_classes_df.to_sql('vehicle_classes', engine, if_exists='append', index=False)
    session.commit()
    
    logger.info(f"Added {len(vehicle_class_data)} vehicle classes")

def process_congestion_entries(engine, session, df):
    """Process and insert congestion entries"""
    logger.info("Processing congestion entries...")
    
    # Get entry point mapping (name to id)
    entry_point_query = session.execute(text("SELECT id, name FROM entry_points"))
    entry_point_map = {row[1]: row[0] for row in entry_point_query}
    
    # Get vehicle class mapping (name to id)
    vehicle_class_query = session.execute(text("SELECT id, name FROM vehicle_classes"))
    vehicle_class_map = {row[1]: row[0] for row in vehicle_class_query}
    
    # Prepare data for congestion entries
    logger.info("Preparing congestion entry data...")
    
    # Filter to rows with valid detection regions
    valid_regions = df['Detection Region'].isin(entry_point_map.keys())
    valid_df = df[valid_regions].copy()
    
    if valid_df.empty:
        logger.warning("No valid entries found after mapping detection regions!")
        return
    
    # Map to entry point IDs and vehicle class IDs
    valid_df['entry_point_id'] = valid_df['Detection Region'].map(entry_point_map)
    valid_df['vehicle_class_id'] = valid_df['Vehicle Class'].map(vehicle_class_map)
    
    # Keep only necessary columns and rename
    entries_df = valid_df[[
        'datetime', 
        'entry_point_id', 
        'vehicle_class_id', 
        'CRZ Entries', 
        'Excluded Roadway Entries',
        'Time Period'
    ]].copy()
    
    entries_df.rename(columns={
        'datetime': 'timestamp',
        'CRZ Entries': 'entry_count',
        'Excluded Roadway Entries': 'excluded_count',
        'Time Period': 'time_period'
    }, inplace=True)
    
    # Add creation timestamp
    entries_df['created_at'] = datetime.utcnow()
    entries_df['updated_at'] = datetime.utcnow()
    
    # Insert in chunks to avoid memory issues
    logger.info(f"Inserting {len(entries_df)} entries in chunks...")
    chunk_size = 10000
    for i in range(0, len(entries_df), chunk_size):
        chunk = entries_df.iloc[i:i+chunk_size]
        chunk.to_sql('congestion_entries', engine, if_exists='append', index=False)
        logger.info(f"Inserted chunk {i//chunk_size + 1}/{(len(entries_df)-1)//chunk_size + 1}")
    
    session.commit()
    logger.info(f"Added {len(entries_df)} congestion entries")

def generate_daily_aggregates(engine, session):
    """Generate daily aggregates for faster queries"""
    logger.info("Generating daily aggregates...")
    
    # Clear existing aggregates
    session.execute(text("DELETE FROM daily_aggregates"))
    session.commit()
    
    # SQL to generate aggregates
    aggregate_sql = """
    INSERT INTO daily_aggregates (date, entry_point_id, vehicle_class_id, total_entries, peak_hour, peak_hour_count)
    SELECT 
        DATE(timestamp) as date,
        entry_point_id,
        vehicle_class_id,
        SUM(entry_count) as total_entries,
        HOUR(timestamp) as peak_hour,
        MAX(hourly_entries) as peak_hour_count
    FROM (
        SELECT 
            timestamp,
            entry_point_id,
            vehicle_class_id,
            entry_count,
            SUM(entry_count) OVER (PARTITION BY DATE(timestamp), HOUR(timestamp), entry_point_id, vehicle_class_id) as hourly_entries
        FROM congestion_entries
    ) AS hourly
    GROUP BY DATE(timestamp), entry_point_id, vehicle_class_id
    """
    
    try:
        session.execute(text(aggregate_sql))
        session.commit()
        
        # Count generated aggregates
        result = session.execute(text("SELECT COUNT(*) FROM daily_aggregates"))
        count = result.scalar()
        logger.info(f"Generated {count} daily aggregates")
    except Exception as e:
        session.rollback()
        logger.error(f"Error generating daily aggregates: {e}")

def run_etl_pipeline(csv_file_path):
    """Run the complete ETL pipeline"""
    logger.info("Starting ETL pipeline...")
    
    try:
        # Connect to database
        engine, session = connect_to_database()
        
        # Load and preprocess data
        df = load_csv_data(csv_file_path)
        df = preprocess_data(df)
        
        # Populate reference tables
        populate_entry_points(engine, session)
        populate_vehicle_classes(engine, session, df)
        
        # Process main data
        process_congestion_entries(engine, session, df)
        
        # Generate aggregates
        generate_daily_aggregates(engine, session)
        
        logger.info("ETL pipeline completed successfully!")
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    csv_file = os.environ.get('CSV_FILE_PATH', 'MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv')
    run_etl_pipeline(csv_file) 