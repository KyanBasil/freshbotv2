"""
Flask application for the Retail Zone Assignment System.
Handles web routes and file uploads for schedule generation.
"""
from flask import Flask, render_template, request, jsonify, session, current_app
from flask_wtf.csrf import CSRFProtect
import json
import csv
import tempfile
import os
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional
import sentry_sdk

from scheduling import generate_schedule
from constants import SKILL_ZONES, SKILLS_DB_PATH, DATETIME_FORMAT
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry SDK before creating the Flask app
sentry_sdk.init(
    dsn="https://63247aa8e98648a5ee4c438764852216@o4508876433326080.ingest.us.sentry.io/4508876444860416",
    # Add data like request headers and IP for users
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for tracing
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True to automatically start the profiler
        "continuous_profiling_auto_start": True,
    },
)

# Initialize Flask app with configuration
app = Flask(__name__)
app.config.from_object(get_config())

# Initialize CSRF protection
csrf = CSRFProtect(app)

@lru_cache(maxsize=1)
def load_employees() -> List[Dict]:
    """
    Load and cache employee data from skills database.
    Returns an empty list if the file doesn't exist or is invalid.
    """
    try:
        if os.path.exists(SKILLS_DB_PATH):
            with open(SKILLS_DB_PATH) as file:
                data = json.load(file)
                return data.get('employees', [])
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading skills database: {e}")
    return []

# Load employee data
employees = load_employees()
employee_skills = {emp['alias']: emp['skills'] for emp in employees}

def validate_csv_content(file_path: str) -> bool:
    """
    Validate CSV file content format.
    Returns True if valid, False otherwise.
    """
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            required_fields = {'Alias', 'Start Time', 'End Time'}
            if not required_fields.issubset(reader.fieldnames):
                logger.error("Missing required CSV fields")
                return False
            
            for row in reader:
                # Validate datetime formats
                try:
                    datetime.strptime(row['Start Time'], DATETIME_FORMAT)
                    datetime.strptime(row['End Time'], DATETIME_FORMAT)
                except ValueError:
                    logger.error(f"Invalid datetime format in row: {row}")
                    return False
                
                # Validate employee exists in skills database
                if row['Alias'] not in employee_skills:
                    logger.error(f"Unknown employee alias in CSV: {row['Alias']}")
                    return False
                    
        return True
    except Exception as e:
        logger.error(f"Error validating CSV: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """Handle file upload and schedule generation."""
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file selected for upload.'}), 400
            
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Unsupported file type. Please upload a CSV file.'}), 400
            
        temp_file = None
        try:
            # Save and validate uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                file.save(temp_file.name)
                if not validate_csv_content(temp_file.name):
                    return jsonify({'error': 'Invalid CSV format or content.'}), 400
                    
                schedule = generate_schedule(temp_file.name)
                session['schedule'] = schedule
                return jsonify({'redirect': '/schedule'})
                
        except Exception as e:
            logger.error(f"Error processing upload: {e}")
            return jsonify({'error': 'An error occurred processing the file.'}), 500
            
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.error(f"Error cleaning up temp file: {e}")

    return render_template('upload.html')

@app.route('/upload_demo_schedule', methods=['POST'])
def upload_demo_schedule():
    """Handle demo schedule generation using sample data."""
    demo_file_path = 'schedule.csv'
    
    if not os.path.exists(demo_file_path):
        logger.error("Demo schedule file not found")
        return jsonify({'error': 'Demo schedule file not found.'}), 404
        
    try:
        if not validate_csv_content(demo_file_path):
            return jsonify({'error': 'Invalid demo schedule format.'}), 500
            
        schedule = generate_schedule(demo_file_path)
        session['schedule'] = schedule
        return jsonify({'redirect': '/schedule'})
        
    except Exception as e:
        logger.error(f"Error generating demo schedule: {e}")
        return jsonify({'error': 'Error generating demo schedule.'}), 500

@app.route('/schedule')
def show_schedule():
    """Display the generated schedule."""
    schedule = session.get('schedule')
    if not schedule:
        logger.warning("Attempted to view schedule without generating one first")
        return render_template('error.html', 
                             message="No schedule found. Please upload a CSV file first."), 404
    
    return render_template('schedule.html', schedule=schedule, zones=SKILL_ZONES)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('error.html', message="Page not found."), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', 
                         message="An internal error occurred. Please try again later."), 500

if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs('static', exist_ok=True)
    
    # Run the application
    app.run(host='0.0.0.0', port=5000)
