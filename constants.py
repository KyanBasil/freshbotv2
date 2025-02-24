"""
Constants used throughout the application.
"""

# Skill zone definitions
SKILL_ZONES = {
    'ENT': 'Entrance',
    'CSH': 'Cashier',
    'CSS': 'Customer Service',
    'ACO': 'ACO'
}

# Valid skills for validation
VALID_SKILLS = set(SKILL_ZONES.keys())

# Date format for CSV parsing
DATETIME_FORMAT = '%Y-%m-%d %H:%M'

# File paths
SKILLS_DB_PATH = 'skills_database.json'
SCHEDULE_IMAGE_PATH = 'static/schedule.png'

# Schedule table settings
DEFAULT_SCHEDULE_LIMIT = 100  # Maximum number of entries to display per page
