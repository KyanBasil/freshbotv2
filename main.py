
import csv

# Data Representation
employees = {
	"kempkyan": {"start": "09:00", "end": "13:00", "skills": ["CS", "CHR"]},
	"fizzyfiz": {"start": "09:00", "end": "13:00", "skills": ["ALC", "ENT"]},
	"jennfowl": {"start": "12:00", "end": "17:00", "skills": ["CS", "CHR"]},
	"night1": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT"]},
	"night2": {"start": "12:00", "end": "17:00", "skills": ["CS", "CHR"]},
	"night3": 	{"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT"]} , # All-day availability
}
zones = {
	"CS": {"capacity": 1},
	"CHR": {"capacity": 1},
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
	employee_skills = employees[employee]["skills"]
	required_skills = zone_requirements.get(zone_id, [])  
	return all(skill in employee_skills for skill in required_skills) 
 

def match_employees_to_zones():
	print("------ Starting Initial Assignments ----------")
	schedule = {}
	errors = []
	
	for hour in range(9, 17):  
		employee_usage = {emp: 0 for emp in employees}  # Reset usage for each run

		available_employees = [(emp, data) for emp, data in employees.items()
			if int(data["start"][:2]) <= hour < int(data["end"][:2])]

		print("------ HOUR:", hour, "---------")
		print("Available Employees:", available_employees)

		for zone_id, zone_data in zones.items():
			zone_data_copy = zone_data.copy()
			if zone_data_copy["capacity"] > 0:
				if available_employees:
					for employee, _data in available_employees:
						if employee_usage[employee] == 0 and has_required_skills(employee, zone_id): # Skill check added
							schedule.setdefault(zone_id, []).append((employee, hour))
							zone_data_copy["capacity"] -= 1
							employee_usage[employee] += 1
							break
					else:
						print(f"Adding 'TBA' for Zone: {zone_id} at Hour: {hour}")  # Insert the line here
						errors.append(f"No employee available for Zone {zone_id} at {hour}:00")
						schedule.setdefault(zone_id, []).append(('TBA', hour))

		for zone_id, assignments in schedule.items():
			for i, (employee, hour) in enumerate(assignments):
				if employee == 'TBA':
					print("Resolving TBA for Zone:", zone_id, "Hour:", hour) # Add this line
					later_employees = [(emp, data) for emp, data in employees.items() if int(data["start"][:2]) > hour]

					if later_employees and zone_data_copy["capacity"] > 0:
						for emp, _data in later_employees:
							if employee_usage[emp] == 0:
								schedule[zone_id][i] = (emp, hour)
								employee_usage[emp] += 1
								zone_data_copy["capacity"] -= 1
								break
						else:
							print("Assigning 'BOH' to Zone:", zone_id, "Hour:", hour) # Add this line
							schedule[zone_id][i] = ('BOH', hour)
							
	return schedule, errors 

# Execute the matching logic
result, errors = match_employees_to_zones()

# CSV Output
with open('schedule.csv', 'w', newline='') as csvfile:
	fieldnames = ['Zone', 'Employee', 'Start', 'End']
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

	writer.writeheader()
	for zone_id, assignments in result.items():
		for hour in range(9, 17):
			found = False
			for employee, assigned_hour in assignments: 
				if assigned_hour == hour: 
					start_time = f"{hour}:00"
					end_time = f"{hour + 1}:00"
					writer.writerow({'Zone': zone_id, 'Employee': employee, 'Start': start_time, 'End': end_time})
					found = True
					break
			if not found:
				writer.writerow({'Zone': zone_id, 'Employee': '', 'Start': f"{hour}:00", 'End': f"{hour + 1}:00"})

# Print any errors that occurred
if errors:
	print("Errors during matching:")
	for error in errors:
		print(error)
