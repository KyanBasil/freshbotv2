import csv

# Data Representation
employees = {
	"kempkyan": {"start": "09:00", "end": "13:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
	"fizzyfiz": {"start": "10:00", "end": "13:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
	"jennfowl": {"start": "11:00", "end": "17:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
	"night1": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
	"night2": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
	"night3": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
	"night4": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT"]},
}

zones = {
	"CHR": {"capacity": 1},
	"CS": {"capacity": 1},
	"ENT": {"capacity": 1},
	"ALC": {"capacity": 1}
}

zone_requirements = {
	"CS": ["CS"],
	"CHR": ["CHR"],
	"ENT": ["ENT"],
	"ALC": ["ALC"]
}

def has_required_skills(employee, zone_id):
	"""Check if an employee has the required skills for a zone."""
	employee_skills = employees[employee]["skills"]
	required_skills = zone_requirements.get(zone_id, [])
	return all(skill in employee_skills for skill in required_skills)

def calculate_penalty(consecutive_hours):
	"""Calculate the penalty for consecutive hours worked."""
	if consecutive_hours <= 2:
		return 0  # No penalty within the preferred limit
	else:
		return consecutive_hours - 2  # Penalty increases linearly after two hours

def find_best_employee(available_employees, zone_id, hour, employee_usage, schedule, errors):
	"""Find the best employee for a given zone and hour."""
	best_employee = None
	best_penalty = float("inf")

	for employee, _data in available_employees:
		penalty = calculate_penalty(employee_usage[employee]['used'])

		if (penalty < best_penalty and has_required_skills(employee, zone_id) and
			hour not in employee_usage[employee]['assignments']):

			if any(zone_id == assigned_zone for assigned_zone, _ in schedule.get(employee, [])):
				errors.append(f"Employee {employee} is already assigned to zone {zone_id} in the same timeslot")
				continue

			best_employee = employee
			best_penalty = penalty

	return best_employee

def assign_employee_to_zone(employee, zone_id, hour, employee_usage, zone_data_copy, schedule):
	"""Assign an employee to a zone for a given hour."""
	schedule.setdefault(zone_id, []).append((employee, hour))
	zone_data_copy["capacity"] -= 1
	employee_usage[employee]['used'] += 1
	employee_usage[employee]['current_zone'] = zone_id
	employee_usage[employee]['assignments'][hour] = zone_id

def match_employees_to_zones(employees):
	"""Match employees to zones based on availability and requirements."""
	schedule = {}
	errors = []
	employee_usage = {emp: {'used': 0, 'current_zone': None, 'assignments': {}} for emp in employees}

	for hour in range(9, 17):
		available_employees = [(emp, data) for emp, data in employees.items()
							   if int(data["start"][:2]) <= hour < int(data["end"][:2])]

		for zone_id, zone_data in zones.items():
			zone_data_copy = zone_data.copy()

			if zone_data_copy["capacity"] > 0:
				if available_employees:
					best_employee = find_best_employee(available_employees, zone_id, hour, employee_usage, schedule, errors)
					if best_employee:
						assign_employee_to_zone(best_employee, zone_id, hour, employee_usage, zone_data_copy, schedule)
				else:
					schedule.setdefault(zone_id, []).append(('TBA', hour))

	return schedule, errors

def resolve_tba_assignments(schedule, errors, employee_usage):
	"""Resolve 'TBA' assignments by assigning available employees."""
	for zone_id, assignments in schedule.items():
		for i, (employee, hour) in enumerate(assignments):
			if employee == 'TBA':
				later_employees = [(emp, data) for emp, data in employees.items() if int(data["start"][:2]) > hour]

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

def write_schedule_to_csv(schedule):
	"""Write the schedule to a CSV file."""
	with open('schedule.csv', 'w', newline='') as csvfile:
		fieldnames = ['Zone', 'Employee', 'Start', 'End']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()

		for zone_id, assignments in schedule.items():
			for hour in range(9, 17):
				found = False
				for employee, assigned_hour in assignments:
					if assigned_hour == hour:
						start_time = f"{hour:02d}:00"
						end_time = f"{hour + 1:02d}:00"
						writer.writerow({'Zone': zone_id, 'Employee': employee, 'Start': start_time, 'End': end_time})
						found = True
						break

				if not found:
					start_time = f"{hour:02d}:00"
					end_time = f"{hour + 1:02d}:00"
					writer.writerow({'Zone': zone_id, 'Employee': 'BOH', 'Start': start_time, 'End': end_time})

def print_errors(errors):
	"""Print any errors that occurred during the matching process."""
	if errors:
		print("Errors during matching:")
		for error in errors:
			print(error)
	else:
		print("No errors occurred during matching.")

# Main program
schedule, errors = match_employees_to_zones(employees)
employee_usage = {emp: {'used': 0, 'current_zone': None, 'assignments': {}} for emp in employees}
resolve_tba_assignments(schedule, errors, employee_usage)
write_schedule_to_csv(schedule)
print_errors(errors)
