import csv
import json
from typing import List, Dict, Tuple, Any

class Employee:
    def __init__(self, employee_id: str, start_time: str, end_time: str, skills: List[str]):
        self.employee_id = employee_id
        self.start_time = start_time
        self.end_time = end_time
        self.skills = skills
        self.assignments: Dict[int, str] = {}
        self.consecutive_hours = 0

    def is_available(self, hour: int) -> bool:
        return int(self.start_time[:2]) <= hour < int(self.end_time[:2])

    def has_required_skills(self, zone_id: str, zone_requirements: Dict[str, List[str]]) -> bool:
        required_skills = zone_requirements.get(zone_id, [])
        return all(skill in self.skills for skill in required_skills)

    def assign_to_zone(self, zone_id: str, hour: int):
        self.assignments[hour] = zone_id
        self.consecutive_hours += 1

class Zone:
    def __init__(self, zone_id: str, capacity: int):
        self.zone_id = zone_id
        self.capacity = capacity

def load_data(zones_file: str, employees_file: str) -> Tuple[Dict[str, Zone], Dict[str, List[str]], Dict[str, Employee]]:
    with open(zones_file) as f:
        data = json.load(f)
        zones = {zone_id: Zone(zone_id, capacity) for zone_id, capacity in data['zones'].items()}
        zone_requirements = data['zone_requirements']

    with open(employees_file) as f:
        data = json.load(f)
        employees = {employee_id: Employee(employee_id, employee_data['start'], employee_data['end'], employee_data['skills'])
                     for employee_id, employee_data in data.items()}

    return zones, zone_requirements, employees

def find_best_employee(available_employees: List[Employee], zone_id: str, hour: int, zone_requirements: Dict[str, List[str]]) -> Employee | None:
    min_consecutive_hours = float('inf')
    best_employee = None

    for employee in available_employees:
        if employee.has_required_skills(zone_id, zone_requirements) and hour not in employee.assignments:
            if employee.consecutive_hours < min_consecutive_hours:
                min_consecutive_hours = employee.consecutive_hours
                best_employee = employee

    return best_employee

def match_employees_to_zones(zones: Dict[str, Zone], zone_requirements: Dict[str, List[str]], employees: Dict[str, Employee]) -> Tuple[Dict[str, List[Tuple[str, int]]], List[str]]:
    schedule: Dict[str, List[Tuple[str, int]]] = {}
    errors: List[str] = []

    for hour in range(8, 22):
        for zone in zones.values():
            if zone.capacity > 0:
                available_employees = [employee for employee in employees.values() if employee.is_available(hour)]
                best_employee = find_best_employee(available_employees, zone.zone_id, hour, zone_requirements)

                if best_employee:
                    best_employee.assign_to_zone(zone.zone_id, hour)
                    zone.capacity -= 1
                    schedule.setdefault(zone.zone_id, []).append((best_employee.employee_id, hour))
                else:
                    schedule.setdefault(zone.zone_id, []).append(('Unassigned', hour))

    return schedule, errors


def resolve_unassigned_slots(schedule: Dict[str, List[Tuple[str, int]]], employees: Dict[str, Employee], zone_requirements: Dict[str, List[str]]) -> None:
    for zone_id, assignments in schedule.items():
        for i, (employee_id, hour) in enumerate(assignments):
            if employee_id == 'Unassigned':
                for employee in employees.values():
                    if employee.is_available(hour) and employee.has_required_skills(zone_id, zone_requirements) and hour not in employee.assignments:
                        employee.assign_to_zone(zone_id, hour)
                        schedule[zone_id][i] = (employee.employee_id, hour)
                        break

def write_schedule_to_csv(schedule: Dict[str, List[Tuple[str, int]]]) -> None:
    fieldnames = ['Zone', 'Employee', 'Start', 'End']
    with open('schedule.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for zone_id, assignments in schedule.items():
            for hour in range(8, 22):
                employee_id = 'Unassigned'
                for emp_id, assigned_hour in assignments:
                    if assigned_hour == hour:
                        employee_id = emp_id
                        break

                start_time = f"{hour:02d}:00"
                end_time = f"{hour + 1:02d}:00"
                writer.writerow({'Zone': zone_id, 'Employee': employee_id, 'Start': start_time, 'End': end_time})

def print_errors(errors: List[str]) -> None:
    if errors:
        print("Errors during matching:")
        for error in errors:
            print(error)
    else:
        print("No errors occurred during matching.")

def main():
    try:
        zones, zone_requirements, employees = load_data('zones.json', 'employees.json')
        schedule, errors = match_employees_to_zones(zones, zone_requirements, employees)
        resolve_unassigned_slots(schedule, employees, zone_requirements)
        write_schedule_to_csv(schedule)
        print_errors(errors)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    else:
        print("Schedule generated successfully.")

if __name__ == "__main__":
    main()
