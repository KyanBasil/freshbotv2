"""
Core scheduling logic for the Retail Zone Assignment System.
Handles employee assignments to zones based on skills and availability.
"""
import csv
import json
import logging
from datetime import datetime
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

    def __post_init__(self):
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

def read_schedule(file_path: str, skills_db: Dict) -> List[Employee]:
    """
    Read and validate the schedule from CSV file.
    
    Args:
        file_path: Path to the schedule CSV file
        skills_db: Loaded skills database
        
    Returns:
        List of Employee objects
        
    Raises:
        ValueError: If the file format is invalid or contains invalid data
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
                    raise ValueError(f"Unknown employee alias in schedule: {alias}")
                    
                try:
                    start_time = datetime.strptime(row['Start Time'], DATETIME_FORMAT)
                    end_time = datetime.strptime(row['End Time'], DATETIME_FORMAT)
                except ValueError as e:
                    raise ValueError(f"Invalid datetime format for {alias}: {e}")
                
                employees.append(Employee(
                    alias=alias,
                    skills=employee_skills_map[alias],
                    start_time=start_time,
                    end_time=end_time
                ))
                
        return employees
        
    except csv.Error as e:
        raise ValueError(f"Error reading CSV file: {e}")

def assign_zones(employees: List[Employee], zones: List[Zone]) -> None:
    """
    Assign employees to zones based on skills and availability.
    
    Args:
        employees: List of Employee objects to assign
        zones: List of Zone objects to assign to
        
    Raises:
        ValueError: If an employee cannot be assigned to any zone
    """
    # Sort employees by start time
    employees.sort(key=lambda x: x.start_time)
    
    for employee in employees:
        assigned = False
        # First pass: try to assign to unoccupied zones
        for zone in zones:
            if (zone.required_skill in employee.skills and 
                employee.start_time not in zone.assignments):
                zone.assignments[employee.start_time] = employee.alias
                assigned = True
                logger.info(f"Assigned {employee.alias} to {zone.name} at {employee.start_time}")
                break
        
        # Second pass: if still unassigned, try any compatible zone
        if not assigned:
            for zone in zones:
                if zone.required_skill in employee.skills:
                    zone.assignments[employee.start_time] = employee.alias
                    assigned = True
                    logger.info(f"Assigned {employee.alias} to {zone.name} at {employee.start_time} (fallback)")
                    break
                    
        if not assigned:
            logger.warning(f"Could not assign {employee.alias} to any zone at {employee.start_time}")

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

def generate_schedule_image(zones: List[Zone]) -> str:
    """
    Generate a visualization of the schedule.
    
    Args:
        zones: List of Zone objects with assignments
        
    Returns:
        Path to the generated image file
        
    Raises:
        RuntimeError: If image generation fails
    """
    try:
        fig, ax = plt.subplots(figsize=(12, 8))
        for zone in zones:
            times = list(zone.assignments.keys())
            aliases = list(zone.assignments.values())
            if times and aliases:
                ax.plot(times, aliases, 'o-', label=zone.name)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator())
        plt.title('Employee Zone Assignments')
        plt.xlabel('Time')
        plt.ylabel('Employee')
        plt.legend()
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
        
        # Generate visualization
        generate_schedule_image(zones)
        
        # Generate and return schedule output
        return generate_output(zones)
        
    except Exception as e:
        logger.error(f"Schedule generation failed: {e}")
        raise
