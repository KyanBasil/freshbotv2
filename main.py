"""
Matches employees to zones based on availability and skill requirements.

The `match_employees_to_zones` function is the main entry point for the employee scheduling logic. It takes a dictionary of employees and their availability and skills, and returns a schedule of employee assignments to zones, as well as a list of any errors that occurred during the matching process.

The function first creates a dictionary to track employee usage, then iterates through each hour of the day and each zone, attempting to assign the best available employee to each zone. The `find_best_employee` function is used to determine the best employee for a given zone and hour, taking into account the employee's skills, availability, and any existing assignments.

If no employee is available for a zone, a 'TBA' (to be assigned) placeholder is added to the schedule. The `resolve_tba_assignments` function is then called to attempt to assign available employees to the 'TBA' slots.

Finally, the `write_schedule_to_csv` function is called to write the final schedule to a CSV file, and the `print_errors` function is called to display any errors that occurred during the matching process.
"""
import csv
from typing import List, Dict, Tuple, Any
from employee import employees


zones: Dict[str, Dict[str, int]] = {
  "CHR": {"capacity": 1},
  "CS": {"capacity": 1},
  "ENT": {"capacity": 1},
  "ALC": {"capacity": 1}
}

zone_requirements: Dict[str, List[str]] = {
  "CS": ["CS"],
  "CHR": ["CHR"],
  "ENT": ["ENT"],
  "ALC": ["ALC"]
}

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
  if consecutive_hours <= 2:
    return 0  # No penalty within the preferred limit
  else:
    return consecutive_hours - 2  # Penalty increases linearly after two hours

def find_best_employee(available_employees: List[Tuple[str, Dict[str, Any]]], zone_id: str, hour: int, employee_usage: Dict[str, Dict[str, Any]], schedule: Dict[str, List[Tuple[str, int]]], errors: List[str]) -> str:
  """Find the best employee for a given zone and hour."""
  best_employee: str = None
  best_penalty: int = float("inf")

  for employee, _data in available_employees:
    penalty: int = calculate_penalty(employee_usage[employee]['used'])

    if (penalty < best_penalty and has_required_skills(employee, zone_id) and
        hour not in employee_usage[employee]['assignments']):

      if any(zone_id == assigned_zone for assigned_zone, _ in schedule.get(employee, [])):
        errors.append(f"Employee {employee} is already assigned to zone {zone_id} in the same timeslot")
        continue

      best_employee = employee
      best_penalty = penalty

  return best_employee

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

  for hour in range(9, 17):
    available_employees: List[Tuple[str, Dict[str, Any]]] = [(emp, data) for emp, data in employees.items()
                           if int(data["start"][:2]) <= hour < int(data["end"][:2])]

    for zone_id, zone_data in zones.items():
      zone_data_copy: Dict[str, int] = zone_data.copy()

      if zone_data_copy["capacity"] > 0:
        if available_employees:
          best_employee: str = find_best_employee(available_employees, zone_id, hour, employee_usage, schedule, errors)
          if best_employee:
            assign_employee_to_zone(best_employee, zone_id, hour, employee_usage, zone_data_copy, schedule)
        else:
          schedule.setdefault(zone_id, []).append(('TBA', hour))

  return schedule, errors

def resolve_tba_assignments(schedule: Dict[str, List[Tuple[str, int]]], errors: List[str], employee_usage: Dict[str, Dict[str, Any]]) -> None:
  """Resolve 'TBA' assignments by assigning available employees."""
  for zone_id, assignments in schedule.items():
    for i, (employee, hour) in enumerate(assignments):
      if employee == 'TBA':
        later_employees: List[Tuple[str, Dict[str, Any]]] = [(emp, data) for emp, data in employees.items() if int(data["start"][:2]) > hour]

        if later_employees and zones[zone_id]["capacity"] > 0:
          for emp, _data in later_employees:
            if any(zone_id == assigned_zone for assigned_zone, _ in schedule.get(emp, [])):
              errors.append(f"Employee {emp} is already assigned to zone {zone_id} in the same timeslot")
              continue

            schedule[zone_id][i] = (emp, hour)
            employee_usage[emp]['used'] += 1
            employee_usage[emp]['current_zone'] = zone_id
            employee_usage[emp]['assignments'][hour] = zone_id
            zones[zone_id]["capacity"] -= 1
            break

def write_schedule_to_csv(schedule: Dict[str, List[Tuple[str, int]]]) -> None:
  """Write the schedule to a CSV file."""
  with open('schedule.csv', 'w', newline='') as csvfile:
    fieldnames: List[str] = ['Zone', 'Employee', 'Start', 'End']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for zone_id, assignments in schedule.items():
      for hour in range(9, 17):
        found: bool = False
        for employee, assigned_hour in assignments:
          if assigned_hour == hour:
            start_time: str = f"{hour:02d}:00"
            end_time: str = f"{hour + 1:02d}:00"
            writer.writerow({'Zone': zone_id, 'Employee': employee, 'Start': start_time, 'End': end_time})
            found = True
            break

        if not found:
          start_time: str = f"{hour:02d}:00"
          end_time: str = f"{hour + 1:02d}:00"
          writer.writerow({'Zone': zone_id, 'Employee': 'BOH', 'Start': start_time, 'End': end_time})

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

  write_schedule_to_csv(schedule)

except ValueError as e:
  print("Invalid employee data:", e)
  
except Exception as e:
  print("Error generating schedule:", e)

else:
  print("Schedule generated successfully")

finally:
  print("Process complete")

print_errors(errors)

