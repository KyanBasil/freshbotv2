import csv
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from prettytable import PrettyTable
import os


class Employee:
    def __init__(self, alias, skills):
        self.alias = alias
        self.skills = skills
        self.schedule = []

class Zone:
    def __init__(self, name, required_skill):
        self.name = name
        self.required_skill = required_skill
        self.assignments = {}

def load_skills_database(file_path):
    with open(file_path, 'r') as jsonfile:
        data = json.load(jsonfile)
    return {employee['alias']: employee['skills'] for employee in data['employees']}

def read_schedule(file_path, skills_db):
    employees = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            alias = row['Alias']
            if alias not in skills_db:
                print(f"Warning: No skills found for {alias}")
                continue
            skills = skills_db[alias]
            start_time = datetime.strptime(row['Start Time'], '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(row['End Time'], '%Y-%m-%d %H:%M')
            
            employee = Employee(alias, skills)
            employee.schedule.append((start_time, end_time))
            employees.append(employee)
    return employees

def assign_zones(employees, zones):
    employees.sort(key=lambda e: e.schedule[0][0])
    
    for employee in employees:
        start_time, end_time = employee.schedule[0]
        current_time = start_time
        
        while current_time < end_time:
            for zone in zones:
                if zone.required_skill in employee.skills and current_time not in zone.assignments:
                    zone.assignments[current_time] = employee
                    break
            current_time += timedelta(hours=1)

def generate_output(zones):
    for zone in zones:
        print(f"\nZone: {zone.name} (Skill: {zone.required_skill})")
        for time, employee in sorted(zone.assignments.items()):
            print(f"{time.strftime('%Y-%m-%d %H:%M')}: {employee.alias}")

def generate_schedule_image(zones, output_file='schedule.png'):
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.Set3(np.linspace(0, 1, len(zones)))
    
    for i, zone in enumerate(zones):
        for time, employee in zone.assignments.items():
            ax.bar(time, 1, width=1/24, bottom=i, color=colors[i], 
                   align='edge', edgecolor='black', linewidth=0.5)
            ax.text(time, i+0.5, employee.alias, ha='left', va='center', 
                    fontsize=8, rotation=90)

    ax.set_yticks(range(len(zones)))
    ax.set_yticklabels([zone.name for zone in zones])
    ax.set_xlabel('Time')
    ax.set_title('Zone Assignments Schedule')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Schedule image saved as {output_file}")

import os
from prettytable import PrettyTable
from datetime import datetime, timedelta

def generate_printable_schedule(zones):
    # Set the store hours
    start_time = datetime.combine(datetime.today(), datetime.min.time()).replace(hour=8)
    end_time = datetime.combine(datetime.today(), datetime.min.time()).replace(hour=22)

    table = PrettyTable()
    table.field_names = ["Time"] + [zone.name for zone in zones]

    current_time = start_time
    while current_time <= end_time:
        row = [current_time.strftime('%H:%M')]
        for zone in zones:
            employee = zone.assignments.get(current_time, None)
            row.append(employee.alias if employee else "-")
        table.add_row(row)
        current_time += timedelta(hours=1)

    print(table)

    try:
        with open('printable_schedule.txt', 'w') as f:
            f.write(str(table))
        print("Printable schedule successfully saved as printable_schedule.txt")
    except IOError as e:
        print(f"Error writing to file: {e}")

    if os.path.exists('printable_schedule.txt'):
        print("File creation verified.")
    else:
        print("File was not created. Please check permissions and disk space.")

# Main program
zones = [
    Zone("Entrance", "ENT"),
    Zone("Cashier", "CSH"),
    Zone("Customer Service", "CSS"),
    Zone("ACO", "ACO")
]

skills_db = load_skills_database('skills_database.json')
employees = read_schedule('schedule.csv', skills_db)
assign_zones(employees, zones)
generate_output(zones)
generate_schedule_image(zones)
generate_printable_schedule(zones)
