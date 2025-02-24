"""
Command-line interface for the Retail Zone Assignment System.
Generates schedule and outputs visualization and text-based reports.
"""
import logging
import os
from scheduling import (
    generate_schedule,
    generate_schedule_image,
    generate_printable_schedule,
    Zone
)
from constants import SKILL_ZONES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Generate schedule and create outputs."""
    try:
        # Define zones based on constants
        zones = [
            Zone(name=name, required_skill=skill)
            for skill, name in SKILL_ZONES.items()
        ]
        
        # Generate schedule
        logger.info("Generating schedule...")
        schedule = generate_schedule('schedule.csv')
        
        # Generate visualization
        logger.info("Creating schedule visualization...")
        image_path = generate_schedule_image(zones)
        logger.info(f"Schedule image saved to: {image_path}")
        
        # Generate text report
        logger.info("Creating printable schedule...")
        printable = generate_printable_schedule(zones)
        with open('printable_schedule.txt', 'w', encoding='utf_8') as f:
            f.write(printable)
        logger.info("Printable schedule saved to: printable_schedule.txt")
        
        logger.info("Schedule generation complete!")
        
    except Exception as e:
        logger.error(f"Schedule generation failed: {e}")
        raise

if __name__ == '__main__':
    main()
