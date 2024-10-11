import csv
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from prettytable import PrettyTable
import os
from scheduling import load_skills_database, read_schedule, assign_zones, generate_output, generate_schedule_image, generate_printable_schedule


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
