from flask import Flask, render_template, request
import json
import csv
from datetime import datetime, timedelta

app = Flask(__name__)

# Read employee data from JSON file
with open('employees.json') as file:
    employees = json.load(file)

# Create a dictionary to store employee names and their skills
employee_skills = {emp['name']: emp['skills'] for emp in employees}

# Define skill zones
skill_zones = {
    'BA': 'Brand Ambassador',
    'CHR': 'Cashier',
    'CS': 'Customer Service',
    'ENT': 'Entrance'
}

def generate_schedule():
    # Read the daily schedule from the CSV file
    daily_schedule = []
    with open('daily_schedule.csv', 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['name'] in employee_skills:
                daily_schedule.append(row)

    # Sort the daily schedule by start time
    sorted_daily_schedule = sorted(daily_schedule, key=lambda emp: emp['start'])

    # Define start and end times for the schedule
    start_time = datetime.strptime('08:00', '%H:%M')
    end_time = datetime.strptime('22:00', '%H:%M')

    # Initialize schedule dictionary
    schedule = {}

    # Generate time slots from 8am to 10pm with 30-minute intervals
    current_time = start_time
    while current_time <= end_time:
        time_str = current_time.strftime('%I:%M %p')
        schedule[time_str] = {zone: 'No employee assigned' for zone in skill_zones.values()}
        current_time += timedelta(minutes=30)

    # Iterate over sorted daily schedule
    for employee in sorted_daily_schedule:
        emp_start_time = datetime.strptime(employee['start'], '%H:%M')
        emp_end_time = datetime.strptime(employee['end'], '%H:%M')

        # Iterate over each 30-minute interval of the employee's shift
        current_time = emp_start_time
        while current_time < emp_end_time:
            time_str = current_time.strftime('%I:%M %p')

            # Check if the current time slot is within the schedule range
            if start_time <= current_time <= end_time:
                # Assign employee to appropriate skill zone based on the defined order
                for skill in ['BA', 'CHR', 'CS', 'ENT']:
                    if skill in employee_skills[employee['name']]:
                        zone = skill_zones[skill]
                        if schedule[time_str][zone] == 'No employee assigned':
                            schedule[time_str][zone] = employee['name']
                            break

            # Move to the next 30-minute interval
            current_time += timedelta(minutes=30)

    # Convert schedule keys to datetime objects for sorting
    schedule_sorted = {datetime.strptime(time_str, '%I:%M %p'): zones for time_str, zones in schedule.items()}

    return schedule_sorted

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Save the uploaded file
            file.save('daily_schedule.csv')

            # Process the CSV file and generate the schedule
            schedule = generate_schedule()

            return render_template('schedule.html', schedule=schedule)

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
