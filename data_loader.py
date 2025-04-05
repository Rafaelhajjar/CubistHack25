import os
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your SQLAlchemy models (ensure init_db.py is correct)
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
    """Connect to database, load CSV data, and insert it into SQLite."""
    # 1. Define the database connection
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'app.db')
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 2. Load the CSV data
        csv_file = 'MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv'
        full_csv_path = os.path.join(base_dir, csv_file)
        
        if not os.path.exists(full_csv_path):
            raise FileNotFoundError(f"CSV file not found at {full_csv_path}")
        
        print(f"Loading CSV data from: {full_csv_path}")
        df = pd.read_csv(full_csv_path)
        print(f"Loaded {len(df)} rows from CSV.")
        
        # 3. Preprocess data
        print("Preprocessing data...")
        
        # Convert date/time column
        if 'Toll 10 Minute Block' not in df.columns:
            raise KeyError("CSV missing required column: 'Toll 10 Minute Block'")
        df['datetime'] = pd.to_datetime(df['Toll 10 Minute Block'], errors='coerce')
        df.dropna(subset=['datetime'], inplace=True)
        
        # Convert CRZ Entries to integer
        if 'CRZ Entries' not in df.columns:
            raise KeyError("CSV missing required column: 'CRZ Entries'")
        df['CRZ Entries'] = pd.to_numeric(df['CRZ Entries'], errors='coerce')
        df.dropna(subset=['CRZ Entries'], inplace=True)
        df['CRZ Entries'] = df['CRZ Entries'].astype(int)
        
        # Excluded Roadway Entries (optional column)
        if 'Excluded Roadway Entries' in df.columns:
            df['Excluded Roadway Entries'] = pd.to_numeric(df['Excluded Roadway Entries'], errors='coerce').fillna(0).astype(int)
        else:
            df['Excluded Roadway Entries'] = 0
        
        # Detection Region (should exist)
        if 'Detection Region' not in df.columns:
            raise KeyError("CSV missing required column: 'Detection Region'")
        df['Detection Region'] = df['Detection Region'].astype(str).str.strip()
        
        # Vehicle Class (should exist)
        if 'Vehicle Class' not in df.columns:
            raise KeyError("CSV missing required column: 'Vehicle Class'")
        df['Vehicle Class'] = df['Vehicle Class'].astype(str).str.strip()
        
        # Time Period (optional column)
        if 'Time Period' not in df.columns:
            df['Time Period'] = None
        
        # 4. Populate the `EntryPoint` table
        print("Populating entry points...")
        for name, (lat, lon) in entry_points.items():
            existing = session.query(EntryPoint).filter_by(name=name).first()
            if not existing:
                entry_point = EntryPoint(
                    name=name,
                    latitude=lat,
                    longitude=lon,
                    description=f"Entry point at {name}"
                )
                session.add(entry_point)
        
        # 5. Populate the `VehicleClass` table
        print("Populating vehicle classes...")
        for vehicle_class in df['Vehicle Class'].unique():
            existing = session.query(VehicleClass).filter_by(name=vehicle_class).first()
            if not existing:
                vc = VehicleClass(
                    name=vehicle_class,
                    description=f"Vehicle class: {vehicle_class}"
                )
                session.add(vc)
        
        # Commit these so we can map them
        session.commit()
        
        # 6. Create fast lookup dictionaries
        entry_point_map = {ep.name: ep.id for ep in session.query(EntryPoint).all()}
        vehicle_class_map = {vc.name: vc.id for vc in session.query(VehicleClass).all()}
        
        # 7. Insert congestion entries in batches
        print("Inserting congestion entries in batches...")
        batch_size = 1000
        entries_added = 0
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i : i + batch_size]
            
            for _, row in batch_df.iterrows():
                ep_name = row['Detection Region']
                vc_name = row['Vehicle Class']
                
                # If the region or vehicle class isn’t recognized, skip
                if ep_name not in entry_point_map or vc_name not in vehicle_class_map:
                    continue
                
                entry = CongestionEntry(
                    timestamp=row['datetime'],
                    entry_point_id=entry_point_map[ep_name],
                    vehicle_class_id=vehicle_class_map[vc_name],
                    entry_count=row['CRZ Entries'],
                    excluded_count=row['Excluded Roadway Entries'],
                    time_period=row['Time Period']  # might be None if not in CSV
                )
                session.add(entry)
                entries_added += 1
            
            # Commit after each batch
            session.commit()
            print(f"Processed {i + len(batch_df)} / {len(df)} rows total. Entries added so far: {entries_added}.")
        
        print(f"Data loading complete! Added {entries_added} congestion entries to the database.")
    
    except Exception as e:
        print(f"[ERROR] Loading data failed: {e}")
        session.rollback()
    
    finally:
        session.close()

if __name__ == "__main__":
    load_data()
