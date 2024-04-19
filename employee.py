# employee.py
from typing import Dict, Any

employees: Dict[str, Dict[str, Any]] = {
  "kempkyan": {"start": "09:00", "end": "13:00", "skills": ["CS"]},
  "fizzyfiz": {"start": "10:00", "end": "13:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
  "jennfowl": {"start": "11:00", "end": "17:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
  "night1": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
  "night2": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
  "night3": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
  "night4": {"start": "12:00", "end": "17:00", "skills": ["ALC", "ENT"]},
  "evening1": {"start": "15:00", "end": "23:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
  "evening2": {"start": "15:00", "end": "23:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
  "evening3": {"start": "15:00", "end": "23:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
  "evening4": {"start": "15:00", "end": "23:00", "skills": ["ALC", "ENT", "CS", "CHR"]},
}


__all__ = ['employees']