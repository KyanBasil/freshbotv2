import random
import csv

# Data Representation
employees = {
	"kempkyan": {"start": "09:00", "end": "13:00"},
	"fizzyfiz": {"start": "10:00", "end": "15:00"},
	"jennfowl": {"start": "12:00", "end": "16:00"},
	"test1": {"start": "09:00", "end": "16:00"} , # All-day availability
	"test2": {"start": "11:00", "end": "17:00"} , # Overlapping availability 
}

zones = {
	"CS": {"capacity": 1},
	"CHR": {"capacity": 1},
	"ENT": {"capacity": 1},
	"ALC": {"capacity": 1}
}

def match_employees_to_zones():
	print("------ Starting Initial Assignments ----------")
	schedule = {}
	errors = []
	employee_usage = {emp: 0 for emp in employees} 

	for hour in range(9, 17): 
		available_employees = [(emp, data) for emp, data in employees.items()
			if int(data["start"][:2]) <= hour < int(data["end"][:2])] # Reset usage
		# print("Employee Usage:", employee_usage) 

		print("------ HOUR:", hour, "---------") # Added debugging line
		print("Available Employees:", available_employees) 

		# Initial Assignment Pass
		for zone_id, zone_data in zones.items():
			zone_data_copy = zone_data.copy() # Create a copy 
			if zone_data_copy["capacity"] > 0:
				print("Zone Capacities:", {zone_id: zone_data["capacity"] for zone_id, zone_data in zones.items()})
				if available_employees:
					employee, data = min(available_employees, key=lambda item: employee_usage[item[0]])  
					schedule.setdefault(zone_id, []).append(('TBA', hour)) # Temporary 'TBA'
					zone_data_copy["capacity"] = 0 # Update the copy
					print("Zone Capacities (After Assignment):", {zone_id: zone_data["capacity"] for zone_id, zone_data in zones.items()}) # Debugging line
					employee_usage[employee] += 1 
				else:
					print(f"No employee available at {hour}:00 for Zone: {zone_id}")
					print("Available Employees:", available_employees) # Added debugging line
					schedule.setdefault(zone_id, []).append(('TBA', hour))


	# Second Pass - Resolve 'TBA' 
				for zone_id, assignments in schedule.items():
					zone_capacities_snapshot = {zone_id: zone_data["capacity"] for zone_id, zone_data in zones.items()} # Create a copy
					for i, (employee, hour) in enumerate(assignments):
						if employee == 'TBA':
							print("BEFORE Zone Capacities:", zone_capacities_snapshot)  # Use the snapshot
				later_employees = [(emp, data) for emp, data in employees.items()
								 if int(data["start"][:2]) > hour] # Employees starting later
				if later_employees:
					employee, data = min(later_employees, key=lambda item: employee_usage[item[0]])
					schedule[zone_id][i] = (employee, hour) # Replace 'TBA'
					employee_usage[employee] += 1
				else:
					schedule[zone_id][i] = ('BOH', hour) # True 'last resort'
				print("AFTER Zone Capacities:", zone_capacities_snapshot)

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
					break # No need to check other employees for this hour
			if not found:
				writer.writerow({'Zone': zone_id, 'Employee': 'BOH', 'Start': f"{hour}:00", 'End': f"{hour + 1}:00"})



# Print any errors that occurred
if errors:
	print("Errors during matching:")
	for error in errors:
		print(error)
