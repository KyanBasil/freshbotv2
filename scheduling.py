import csv
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from prettytable import PrettyTable
import os

def load_skills_database(file_path):
    with open(file_path, 'r') as file:
        skills_db = json.load(file)
    return skills_db

def read_schedule(file_path, skills_db):
    employees = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            alias = row['Alias']
            start_time = datetime.strptime(row['Start Time'], '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(row['End Time'], '%Y-%m-%d %H:%M')
            skills = skills_db['employees'][alias]['skills']
            employees.append(Employee(alias, skills, start_time, end_time))
    return employees

def assign_zones(employees, zones):
    for employee in employees:
        for zone in zones:
            if zone.required_skill in employee.skills:
                zone.assignments[employee.start_time] = employee.alias

def generate_output(zones):
    for zone in zones:
        print(f"Zone: {zone.name}")
        for time, alias in zone.assignments.items():
            print(f"{time.strftime('%H:%M')}: {alias}")

def generate_schedule_image(zones):
    fig, ax = plt.subplots()
    for zone in zones:
        times = list(zone.assignments.keys())
        aliases = list(zone.assignments.values())
        ax.plot(times, aliases, label=zone.name)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator())
    plt.legend()
    plt.show()

def generate_printable_schedule(zones):
    table = PrettyTable()
    table.field_names = ["Time"] + [zone.name for zone in zones]
    times = sorted(set(time for zone in zones for time in zone.assignments.keys()))
    for time in times:
        row = [time.strftime('%H:%M')]
        for zone in zones:
            row.append(zone.assignments.get(time, '-'))
        table.add_row(row)
    print(table)
