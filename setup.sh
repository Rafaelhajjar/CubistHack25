#!/bin/bash

echo "Manhattan Congestion Analytics - Setup Script"
echo "============================================="

# Add Python user bin to PATH
export PATH="/Users/rafaelhajjar/Library/Python/3.9/bin:$PATH"
export PYTHONPATH="/Users/rafaelhajjar/CubistHack25:$PYTHONPATH"

echo "1. Initializing database..."
python3 init_db.py

echo "2. Loading data into database..."
python3 data_loader.py

echo "3. Setup complete! You can now run the app with:"
echo "python3 app.py" 