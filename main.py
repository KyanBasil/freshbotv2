import json
from datetime import datetime, timedelta

# Read employee data from JSON file
with open('employees.json') as file:
    employees = json.load(file)

# Define skill zones
skill_zones = {
    'BA': 'Brand Ambassador',
    'CHR': 'Cashier',
    'CS': 'Customer Service',
    'ENT': 'Entrance'
}

# Sort employees by start time
sorted_employees = sorted(employees, key=lambda emp: emp['start'])

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

# Iterate over sorted employees
for employee in sorted_employees:
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
                if skill in employee['skills']:
                    zone = skill_zones[skill]
                    if schedule[time_str][zone] == 'No employee assigned':
                        schedule[time_str][zone] = employee['name']
                        break

        # Move to the next 30-minute interval
        current_time += timedelta(minutes=30)

# Convert schedule keys to datetime objects for sorting
schedule_sorted = {datetime.strptime(time_str, '%I:%M %p'): zones for time_str, zones in schedule.items()}

# Print the schedule
for time, zones in sorted(schedule_sorted.items()):
    time_str = time.strftime('%I:%M %p')
    print(f"{time_str}:")
    for zone, employee in zones.items():
        print(f"  {zone}: {employee}")
    print()
