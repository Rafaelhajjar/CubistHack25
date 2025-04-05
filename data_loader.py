import os
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from init_db import EntryPoint, VehicleClass, CongestionEntry, DailyAggregate, Base

# Entry Point mapping
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

def load_data():
    """Connect to database and load data"""
    # Define the database connection
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Load the CSV data
        print("Loading CSV data...")
        csv_file = 'MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv'
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} rows from CSV")
        
        # Preprocess data
        print("Preprocessing data...")
        df['datetime'] = pd.to_datetime(df['Toll 10 Minute Block'], errors='coerce')
        df.dropna(subset=['datetime'], inplace=True)
        
        df['CRZ Entries'] = pd.to_numeric(df['CRZ Entries'], errors='coerce')
        df.dropna(subset=['CRZ Entries'], inplace=True)
        df['CRZ Entries'] = df['CRZ Entries'].astype(int)
        
        df['Excluded Roadway Entries'] = pd.to_numeric(df['Excluded Roadway Entries'], errors='coerce')
        df['Excluded Roadway Entries'] = df['Excluded Roadway Entries'].fillna(0).astype(int)
        
        df['Detection Region'] = df['Detection Region'].str.strip()
        
        # Populate entry points
        print("Populating entry points...")
        for name, (lat, lon) in entry_points.items():
            # Check if entry point already exists
            existing = session.query(EntryPoint).filter_by(name=name).first()
            if not existing:
                entry_point = EntryPoint(
                    name=name,
                    latitude=lat,
                    longitude=lon,
                    description=f"Entry point at {name}"
                )
                session.add(entry_point)
        
        # Populate vehicle classes
        print("Populating vehicle classes...")
        for vehicle_class in df['Vehicle Class'].unique():
            # Check if vehicle class already exists
            existing = session.query(VehicleClass).filter_by(name=vehicle_class).first()
            if not existing:
                vc = VehicleClass(
                    name=vehicle_class,
                    description=f"Vehicle class: {vehicle_class}"
                )
                session.add(vc)
        
        # Commit entry points and vehicle classes
        session.commit()
        
        # Create mapping dictionaries for faster lookups
        entry_point_map = {ep.name: ep.id for ep in session.query(EntryPoint).all()}
        vehicle_class_map = {vc.name: vc.id for vc in session.query(VehicleClass).all()}
        
        # Process and insert congestion entries in batches
        print("Inserting congestion entries...")
        batch_size = 1000
        entries_added = 0
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]
            
            for _, row in batch_df.iterrows():
                # Check if entry point and vehicle class exist in our mappings
                if row['Detection Region'] in entry_point_map and row['Vehicle Class'] in vehicle_class_map:
                    entry = CongestionEntry(
                        timestamp=row['datetime'],
                        entry_point_id=entry_point_map[row['Detection Region']],
                        vehicle_class_id=vehicle_class_map[row['Vehicle Class']],
                        entry_count=row['CRZ Entries'],
                        excluded_count=row['Excluded Roadway Entries'],
                        time_period=row['Time Period']
                    )
                    session.add(entry)
                    entries_added += 1
            
            # Commit batch
            session.commit()
            print(f"Processed {i+len(batch_df)} rows, added {entries_added} entries")
        
        print(f"Data loading complete! Added {entries_added} entries to the database.")
    
    except Exception as e:
        print(f"Error loading data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_data() 