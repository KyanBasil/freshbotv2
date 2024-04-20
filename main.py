# main.py
import csv
from typing import List, Dict, Tuple, Any
from employee import *
import json


with open('zones.json') as f:
    data = json.load(f)
    zones = data['zones']
    zone_requirements = data['zone_requirements']

def validate_employee_data(employees: Dict[str, Dict[str, Any]]) -> None:
  errors: List[str] = []
  for emp, data in employees.items():
    if "start" not in data:
      errors.append(f"Missing start time for {emp}")
    if "end" not in data:  
      errors.append(f"Missing end time for {emp}")
    if "skills" not in data:
      errors.append(f"Missing skills for {emp}")

  if errors:
    print("Invalid employee data:")
    for error in errors:
      print(error)
    raise ValueError("Invalid employee data")

# Add this before processing data
validate_employee_data(employees)


def has_required_skills(employee: str, zone_id: str) -> bool:
  """Check if an employee has the required skills for a zone."""
  employee_skills: List[str] = employees[employee]["skills"]
  required_skills: List[str] = zone_requirements.get(zone_id, [])
  return all(skill in employee_skills for skill in required_skills)

def calculate_penalty(consecutive_hours: int) -> int:
    """Calculate the penalty for consecutive hours worked."""
    if consecutive_hours <= 4:
        return 0  # No penalty within the preferred limit
    else:
        return consecutive_hours - 4  # Penalty increases linearly after four hours


def find_best_employee(available_employees: List[Tuple[str, Dict[str, Any]]], zone_id: str, hour: int, employee_usage: Dict[str, Dict[str, Any]], schedule: Dict[str, List[Tuple[str, int]]], errors: List[str]) -> str:
    """Find the best employee for a given zone and hour."""
    def penalty_key(employee_data: Tuple[str, Dict[str, Any]]) -> int:
        employee, _ = employee_data
        return calculate_penalty(employee_usage[employee]['used'])

    filtered_employees = [
        (employee, data) for employee, data in available_employees
        if has_required_skills(employee, zone_id) and hour not in employee_usage[employee]['assignments']
        and not any(zone_id == assigned_zone for assigned_zone, _ in schedule.get(employee, []))
    ]

    if filtered_employees:
        return min(filtered_employees, key=penalty_key)[0]
    else:
        return None


def assign_employee_to_zone(employee: str, zone_id: str, hour: int, employee_usage: Dict[str, Dict[str, Any]], zone_data_copy: Dict[str, int], schedule: Dict[str, List[Tuple[str, int]]]) -> None:
  """Assign an employee to a zone for a given hour."""
  schedule.setdefault(zone_id, []).append((employee, hour))
  zone_data_copy["capacity"] -= 1
  employee_usage[employee]['used'] += 1
  employee_usage[employee]['current_zone'] = zone_id
  employee_usage[employee]['assignments'][hour] = zone_id

def match_employees_to_zones(employees: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, List[Tuple[str, int]]], List[str]]:
    """Match employees to zones based on availability and requirements."""
    schedule: Dict[str, List[Tuple[str, int]]] = {}
    errors: List[str] = []
    employee_usage: Dict[str, Dict[str, Any]] = {emp: {'used': 0, 'current_zone': None, 'assignments': {}} for emp in employees}

    for hour in range(8, 22):
        available_employees: List[Tuple[str, Dict[str, Any]]] = [
            (emp, data) for emp, data in employees.items()
            if int(data["start"][:2]) <= hour < int(data["end"][:2])
        ]

        for zone_id, zone_data in zones.items():
            zone_data_copy: Dict[str, int] = zone_data.copy()

            if zone_data_copy["capacity"] > 0:
                if available_employees:
                    best_employee: str = find_best_employee(available_employees, zone_id, hour, employee_usage, schedule, errors)
                    if best_employee:
                        assign_employee_to_zone(best_employee, zone_id, hour, employee_usage, zone_data_copy, schedule)
                    else:
                        schedule.setdefault(zone_id, []).append(('BOH', hour))  # Changed from 'TBA' to 'BOH'
                else:
                    schedule.setdefault(zone_id, []).append(('BOH', hour))  # Changed from 'TBA' to 'BOH'

    return schedule, errors



def resolve_tba_assignments(schedule: Dict[str, List[Tuple[str, int]]], errors: List[str], employee_usage: Dict[str, Dict[str, Any]]) -> None:
    """Assign available employees to 'BOH' slots if they become available."""
    for zone_id, assignments in schedule.items():
        for i, (employee, hour) in enumerate(assignments):
            if employee == 'BOH':
                later_employees: List[Tuple[str, Dict[str, Any]]] = [
                  (emp, data) for emp, data in employees.items()
                  if int(data["start"][:2]) > hour and int(data["start"][:2]) < int(data["end"][:2])
                ]
                if later_employees:
                    best_employee: str = find_best_employee(later_employees, zone_id, hour, employee_usage, schedule, errors)
                    if best_employee:
                        schedule[zone_id][i] = (best_employee, hour)
                        employee_usage[best_employee]['used'] += 1
                        employee_usage[best_employee]['current_zone'] = zone_id
                        employee_usage[best_employee]['assignments'][hour] = zone_id



def write_schedule_to_csv(schedule: Dict[str, List[Tuple[str, int]]], employee_usage: Dict[str, Dict[str, Any]]) -> None:
    """Write the schedule to a CSV file."""
    with open('schedule.csv', 'w', newline='') as csvfile:
        fieldnames: List[str] = ['Zone', 'Employee', 'Start', 'End', 'Penalty']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        boh_count: int = 0
        consecutive_hours: Dict[str, int] = {}

        for zone_id, assignments in schedule.items():
            for hour in range(8, 22):
                found: bool = False
                for employee, assigned_hour in assignments:
                    if assigned_hour == hour:
                        start_time: str = f"{hour:02d}:00"
                        end_time: str = f"{hour + 1:02d}:00"
                        if employee in consecutive_hours and (employee_usage[employee]['current_zone'] != zone_id or hour - assigned_hour > 1):
                            consecutive_hours[employee] = 0
                        consecutive_hours[employee] = consecutive_hours.get(employee, 0) + 1
                        penalty: int = calculate_penalty(consecutive_hours[employee])
                        print(f"Zone: {zone_id}, Employee: {employee}, Hour: {hour}, Consecutive Hours: {consecutive_hours[employee]}, Penalty: {penalty}")
                        writer.writerow({'Zone': zone_id, 'Employee': employee, 'Start': start_time, 'End': end_time, 'Penalty': penalty})
                        found = True
                        break

                if not found:
                    start_time: str = f"{hour:02d}:00"
                    end_time: str = f"{hour + 1:02d}:00"
                    writer.writerow({'Zone': zone_id, 'Employee': 'BOH', 'Start': start_time, 'End': end_time, 'Penalty': ''})
                    boh_count += 1

        writer.writerow({'Zone': 'Total BOH Slots', 'Employee': str(boh_count), 'Start': '', 'End': '', 'Penalty': ''})

def print_errors(errors: List[str]) -> None:
  """Print any errors that occurred during the matching process."""
  if errors:
    print("Errors during matching:")
    for error in errors:
      print(error)
  else:
    print("No errors occurred during matching.")

# Existing functions 

# Main program
try:
    schedule, errors = match_employees_to_zones(employees)
    employee_usage: Dict[str, Dict[str, Any]] = {emp: {'used': 0, 'current_zone': None, 'assignments': {}} for emp in employees}

    resolve_tba_assignments(schedule, errors, employee_usage)

    write_schedule_to_csv(schedule, employee_usage)

except ValueError as e:
    print("Invalid employee data:", e)

except Exception as e:
    print("Error generating schedule:", e)

else:
    print("Schedule generated successfully")

finally:
    print("Process complete")

print_errors(errors)


