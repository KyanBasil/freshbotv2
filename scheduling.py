"""
Core scheduling logic for the Retail Zone Assignment System.
Handles employee assignments to zones based on skills and availability.
"""
import csv
import json
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from prettytable import PrettyTable
import os
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from constants import (
    SKILL_ZONES,
    VALID_SKILLS,
    DATETIME_FORMAT,
    SKILLS_DB_PATH,
    SCHEDULE_IMAGE_PATH
)

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Employee:
    """Employee data class with schedule and skills information."""
    alias: str
    skills: Set[str]
    start_time: datetime
    end_time: datetime
    break_start: Optional[datetime] = None
    break_end: Optional[datetime] = None
    lunch_start: Optional[datetime] = None
    lunch_end: Optional[datetime] = None

    def __post_init__(self):
        # Validate break times if provided
        if self.break_start or self.break_end:
            if not (self.break_start and self.break_end):
                raise ValueError("Both break start and end times must be provided")
            if self.break_start < self.start_time or self.break_end > self.end_time:
                raise ValueError("Break must be within shift hours")
            if self.break_start >= self.break_end:
                raise ValueError("Break start must be before end")

        # Validate lunch times if provided        
        if self.lunch_start or self.lunch_end:
            if not (self.lunch_start and self.lunch_end):
                raise ValueError("Both lunch start and end times must be provided")
            if self.lunch_start < self.start_time or self.lunch_end > self.end_time:
                raise ValueError("Lunch must be within shift hours")
            if self.lunch_start >= self.lunch_end:
                raise ValueError("Lunch start must be before end")

        # Check for overlapping breaks
        if (self.break_start and self.lunch_start and 
            self.break_start <= self.lunch_end and 
            self.lunch_start <= self.break_end):
            raise ValueError("Break and lunch periods cannot overlap")
        """Validate employee data after initialization."""
        if not self.skills.issubset(VALID_SKILLS):
            invalid_skills = self.skills - VALID_SKILLS
            raise ValueError(f"Invalid skills for employee {self.alias}: {invalid_skills}")
        
        if self.start_time >= self.end_time:
            raise ValueError(f"Invalid schedule for {self.alias}: start time must be before end time")

@dataclass(frozen=True)
class Zone:
    """Zone data class with assignment tracking."""
    name: str
    required_skill: str
    assignments: Dict[datetime, str] = None

    def __post_init__(self):
        """Initialize assignments dictionary if None."""
        if self.assignments is None:
            self.assignments = {}
        
        if self.required_skill not in VALID_SKILLS:
            raise ValueError(f"Invalid required skill for zone {self.name}: {self.required_skill}")

def load_skills_database(file_path: str) -> Dict:
    """
    Load and validate the skills database from JSON file.
    
    Args:
        file_path: Path to the skills database JSON file
        
    Returns:
        Dict containing the skills database
        
    Raises:
        ValueError: If the file format is invalid
        FileNotFoundError: If the file doesn't exist
    """
    try:
        with open(file_path, 'r') as file:
            skills_db = json.load(file)
            
        if 'employees' not in skills_db:
            raise ValueError("Invalid skills database format: missing 'employees' key")
            
        # Validate employee data
        for emp in skills_db['employees']:
            if 'alias' not in emp or 'skills' not in emp:
                raise ValueError(f"Invalid employee data: {emp}")
            if not set(emp['skills']).issubset(VALID_SKILLS):
                raise ValueError(f"Invalid skills for employee {emp['alias']}: {emp['skills']}")
                
        return skills_db
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in skills database: {e}")

def calculate_breaks(start_time: datetime, end_time: datetime) -> tuple:
    """Calculate automatic breaks based on shift duration."""
    shift_duration = (end_time - start_time).total_seconds() / 3600
    break_start = break_end = lunch_start = lunch_end = None
    
    # Calculate short break
    if shift_duration >= MIN_HOURS_BEFORE_BREAK:
        break_start = start_time + timedelta(hours=2)
        break_end = break_start + timedelta(minutes=SHORT_BREAK_DURATION)
    
    # Calculate lunch break
    if shift_duration >= MIN_HOURS_BEFORE_LUNCH:
        lunch_midpoint = start_time + (end_time - start_time)/2
        lunch_start = lunch_midpoint - timedelta(minutes=LUNCH_BREAK_DURATION/2)
        lunch_end = lunch_start + timedelta(minutes=LUNCH_BREAK_DURATION)
        
        # Adjust if lunch overlaps with short break
        if break_start and lunch_start < break_end:
            lunch_start = break_end + timedelta(minutes=30)
            lunch_end = lunch_start + timedelta(minutes=LUNCH_BREAK_DURATION)
    
    return break_start, break_end, lunch_start, lunch_end

def read_schedule(file_path: str, skills_db: Dict) -> List[Employee]:
    """
    Read and validate schedule from CSV file with automatic break calculation.
    
    Args:
        file_path: Path to schedule CSV file
        skills_db: Loaded skills database
        
    Returns:
        List of Employee objects with calculated breaks
        
    Raises:
        ValueError: If invalid data format or content
    """
    employees = []
    employee_skills_map = {emp['alias']: set(emp['skills']) for emp in skills_db['employees']}
    
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            
            if not {'Alias', 'Start Time', 'End Time'}.issubset(reader.fieldnames):
                raise ValueError("CSV missing required fields")
            
            for row in reader:
                alias = row['Alias']
                if alias not in employee_skills_map:
                    raise ValueError(f"Unknown employee alias: {alias}")
                    
                try:
                    start_time = datetime.strptime(row['Start Time'], DATETIME_FORMAT)
                    end_time = datetime.strptime(row['End Time'], DATETIME_FORMAT)
                    
                    # Calculate automatic breaks
                    br_start, br_end, ln_start, ln_end = calculate_breaks(start_time, end_time)
                    
                except ValueError as e:
                    raise ValueError(f"Invalid datetime format for {alias}: {e}")
                
                employees.append(Employee(
                    alias=alias,
                    skills=employee_skills_map[alias],
                    start_time=start_time,
                    end_time=end_time,
                    break_start=br_start,
                    break_end=br_end,
                    lunch_start=ln_start,
                    lunch_end=ln_end
                ))
                
        return employees
        
    except csv.Error as e:
        raise ValueError(f"Error reading CSV file: {e}")

def assign_zones(employees: List[Employee], zones: List[Zone]) -> None:
    """
    Assign employees to zones based on skills and availability,
    accounting for breaks and lunches.
    
    Args:
        employees: List of Employee objects to assign
        zones: List of Zone objects to assign to
        
    Raises:
        ValueError: If an employee cannot be assigned to any zone
    """
    # Create a timeline of events (shift starts, breaks, shift ends)
    timeline = []
    for employee in employees:
        timeline.append((employee.start_time, 'start', employee))
        if employee.break_start:
            timeline.append((employee.break_start, 'break_start', employee))
        if employee.break_end:
            timeline.append((employee.break_end, 'break_end', employee))
        if employee.lunch_start:
            timeline.append((employee.lunch_start, 'lunch_start', employee))
        if employee.lunch_end:
            timeline.append((employee.lunch_end, 'lunch_end', employee))
        timeline.append((employee.end_time, 'end', employee))
    
    # Sort timeline chronologically
    timeline.sort(key=lambda x: x[0])
    
    available_employees = set()
    employee_assignments = {}  # Tracks current zone for each employee
    zone_occupancies = {zone.name: {} for zone in zones}  # Tracks zone assignments
    
    for time, event_type, employee in timeline:
        if event_type == 'start':
            available_employees.add(employee)
            
        elif event_type in ('break_start', 'lunch_start'):
            if employee in available_employees:
                available_employees.remove(employee)
                # Free up any zone assignment during break
                if employee.alias in employee_assignments:
                    zone = employee_assignments.pop(employee.alias)
                    del zone_occupancies[zone.name][time]
            
        elif event_type in ('break_end', 'lunch_end'):
            available_employees.add(employee)
            
        elif event_type == 'end':
            if employee in available_employees:
                available_employees.remove(employee)
                # Free up any zone assignment at end of shift
                if employee.alias in employee_assignments:
                    zone = employee_assignments.pop(employee.alias)
                    del zone_occupancies[zone.name][time]
        
        # Assign available employees to zones
        for emp in list(available_employees):  # Copy for iteration while modifying
            if emp.alias not in employee_assignments:
                # Find first available matching zone
                for zone in zones:
                    if (zone.required_skill in emp.skills and 
                        not zone_occupancies[zone.name].get(time)):
                        # Assign to zone and track occupancy
                        zone_occupancies[zone.name][time] = emp.alias
                        employee_assignments[emp.alias] = zone
                        available_employees.remove(emp)
                        logger.info(f"Assigned {emp.alias} to {zone.name} at {time}")
                        break

    # Convert occupancy tracking to final assignments
    for zone in zones:
        zone.assignments = {
            time: alias 
            for time, alias in sorted(zone_occupancies[zone.name].items())
        }

def generate_output(zones: List[Zone]) -> Dict:
    """
    Generate a formatted output of zone assignments.
    
    Args:
        zones: List of Zone objects with assignments
        
    Returns:
        Dict containing formatted schedule output
    """
    output = {}
    for zone in zones:
        zone_output = {}
        for time, alias in sorted(zone.assignments.items()):
            time_str = time.strftime('%I:%M %p')
            zone_output[time_str] = alias
        output[zone.name] = zone_output
    return output

def generate_schedule_image(zones: List[Zone], employees: List[Employee]) -> str:
    """
    Generate a visualization of the schedule with breaks.
    
    Args:
        zones: List of Zone objects with assignments
        employees: List of Employee objects with break information
        
    Returns:
        Path to the generated image file
        
    Raises:
        RuntimeError: If image generation fails
    """
    try:
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Plot zone assignments
        for zone in zones:
            times = list(zone.assignments.keys())
            aliases = list(zone.assignments.values())
            if times and aliases:
                ax.plot(times, aliases, 'o-', label=zone.name, markersize=8)
                
        # Plot breaks as shaded regions
        for emp in employees:
            # Plot shift duration background
            ax.axvspan(emp.start_time, emp.end_time, alpha=0.05, color='gray')
            
            # Plot breaks
            if emp.break_start and emp.break_end:
                ax.axvspan(emp.break_start, emp.break_end, alpha=0.3, color='red', label='Breaks' if emp == employees[0] else "")
            
            # Plot lunches
            if emp.lunch_start and emp.lunch_end:
                ax.axvspan(emp.lunch_start, emp.lunch_end, alpha=0.3, color='blue', label='Lunches' if emp == employees[0] else "")
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator())
        plt.title('Employee Zone Assignments with Breaks', fontsize=14)
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Employee', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(SCHEDULE_IMAGE_PATH), exist_ok=True)
        plt.savefig(SCHEDULE_IMAGE_PATH)
        plt.close()
        
        return SCHEDULE_IMAGE_PATH
        
    except Exception as e:
        plt.close()  # Ensure figure is closed even if save fails
        raise RuntimeError(f"Failed to generate schedule image: {e}")

def generate_printable_schedule(zones: List[Zone]) -> str:
    """
    Generate a text-based table of the schedule.
    
    Args:
        zones: List of Zone objects with assignments
        
    Returns:
        Formatted string containing the schedule table
    """
    table = PrettyTable()
    table.field_names = ["Time"] + [zone.name for zone in zones]
    
    # Get all unique timestamps
    all_times = set()
    for zone in zones:
        all_times.update(zone.assignments.keys())
    
    # Sort times
    sorted_times = sorted(all_times)
    
    for time in sorted_times:
        row = [time.strftime('%H:%M')]
        for zone in zones:
            row.append(zone.assignments.get(time, '-'))
        table.add_row(row)
    
    return table.get_string()

def generate_schedule(file_path: str) -> Dict:
    """
    Generate a complete schedule from a CSV file.
    
    Args:
        file_path: Path to the schedule CSV file
        
    Returns:
        Dict containing the generated schedule
        
    Raises:
        ValueError: If schedule generation fails due to invalid input
        RuntimeError: If schedule generation fails due to system errors
    """
    try:
        # Define zones based on constants
        zones = [
            Zone(name=name, required_skill=skill)
            for skill, name in SKILL_ZONES.items()
        ]
        
        # Load skills database
        if os.path.exists(SKILLS_DB_PATH):
            skills_db = load_skills_database(SKILLS_DB_PATH)
        else:
            logger.warning(f"Skills database not found at {SKILLS_DB_PATH}")
            skills_db = {"employees": []}
        
        # Read and validate schedule
        employees = read_schedule(file_path, skills_db)
        
        # Assign zones
        assign_zones(employees, zones)
        
        # Generate visualization with employee data
        generate_schedule_image(zones, employees)
        
        # Generate and return schedule output
        return generate_output(zones)
        
    except Exception as e:
        logger.error(f"Schedule generation failed: {e}")
        raise
