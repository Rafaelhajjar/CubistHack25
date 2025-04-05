#!/bin/bash

# Add the Python user bin directory to PATH
export PATH="/Users/rafaelhajjar/Library/Python/3.9/bin:$PATH"
export PYTHONPATH="/Users/rafaelhajjar/CubistHack25:$PYTHONPATH"

echo "PATH updated. Flask command should now be accessible."
echo "You can now run: flask db init" 