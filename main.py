import random
import csv

# Data Representation
employees = {
	"kempkyan": {"start": "09:00", "end": "13:00"},
	"fizzyfiz": {"start": "10:00", "end": "15:00"},
	"jennfowl": {"start": "12:00", "end": "16:00"}
}

zones = {
	"CS": {"capacity": 1},
	"CHR": {"capacity": 1},
	"ENT": {"capacity": 1},
	"ALC": {"capacity": 1}
}

schedule = []  # List to store (employee, zone, hour) tuples


def match_employees_to_zones():
	schedule = {}  
	for hour in range(9, 17): 
		available_employees = [emp for emp, data in employees.items() 
							   if int(data["start"][:2]) <= hour <= int(data["end"][:2])]

		for employee in available_employees:
			for zone_id, zone_data in zones.items():
				if zone_data["capacity"] > 0:
					if zone_id not in schedule:
						schedule[zone_id] = [] 
					schedule[zone_id].append((employee, hour)) 
					zone_data["capacity"] -= 1
					break

	return schedule 

# Execute the matching logic
result = match_employees_to_zones()

# CSV Output
with open('schedule.csv', 'w', newline='') as csvfile: 
	fieldnames = ['Zone', 'Employee', 'Start', 'End'] # Changed fieldnames
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

	writer.writeheader()  
	for zone_id, assignments in result.items(): 
		for employee, hour in assignments:
			start_time = f"{hour}:00"
			end_time = f"{hour + 1}:00" 
			writer.writerow({'Zone': zone_id, 'Employee': employee, 
							 'Start': start_time, 'End': end_time})
