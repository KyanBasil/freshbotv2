from flask import Flask, render_template, request, jsonify, session
import json
import csv
import tempfile
from datetime import datetime, timedelta
from scheduling import generate_schedule

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session handling

# Define a default set of employees
default_employees = [
    {"name": "John Doe", "skills": ["CHR", "CS", "ENT"]},
    {"name": "Jane Smith", "skills": ["CHR", "CS"]},
    {"name": "Alice Johnson", "skills": ["ENT"]},
]

# Read employee data from JSON file
try:
    with open('employees.json') as file:
        employees = json.load(file)
except FileNotFoundError:
    employees = default_employees

# Create a dictionary to store employee names and their skills
employee_skills = {emp['name']: emp['skills'] for emp in employees}

# Define skill zones
skill_zones = {
    'CHR': 'Cashier',
    'CS': 'Customer Service',
    'ENT': 'Entrance'
}

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            if file.filename.endswith('.csv'):
                # Save the uploaded file to a temporary directory
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name

                # Process the CSV file and generate the schedule
                try:
                    schedule = generate_schedule(temp_file_path)
                    session['schedule'] = schedule  # Store the schedule in the session
                    return jsonify({'redirect': '/schedule'})
                except Exception as e:
                    error_message = str(e)
                    return jsonify({'error': error_message}), 500
            else:
                return jsonify({'error': 'Unsupported file type. Please upload a CSV file.'}), 400
        else:
            return jsonify({'error': 'No file selected for upload.'}), 400

    return render_template('upload.html')

@app.route('/upload_demo_schedule', methods=['POST'])
def upload_demo_schedule():
    demo_file_path = 'daily_schedule.csv'
    try:
        schedule = generate_schedule(demo_file_path)
        session['schedule'] = schedule  # Store the schedule in the session
        return jsonify({'redirect': '/schedule'})
    except Exception as e:
        error_message = str(e)
        return jsonify({'error': error_message}), 500

@app.route('/schedule')
def show_schedule():
    # Retrieve the generated schedule from the session
    schedule = session.get('schedule')
    if schedule:
        # Sort the schedule by time
        schedule_sorted = dict(sorted(schedule.items(), key=lambda x: datetime.strptime(x[0], '%I:%M %p')))
        return render_template('schedule.html', schedule=schedule_sorted)
    else:
        return "No schedule found. Please upload a CSV file first."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
