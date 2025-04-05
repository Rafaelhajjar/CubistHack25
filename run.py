import os
from dotenv import load_dotenv
from app import create_app
from config import config

# Load environment variables
load_dotenv()

# Get application environment
app_env = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[app_env])

if __name__ == '__main__':
    # Set debug mode based on environment
    debug = app_env == 'development'
    
    # Run the app on port 5001 instead of 5000
    app.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', 5001))) 