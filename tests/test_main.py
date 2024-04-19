import unittest
from main import calculate_penalty, find_best_employee

class TestFindBestEmployee(unittest.TestCase):

    def test_find_best_employee_basic(self):
        available_employees = [('Alice', {}), ('Bob', {})]
        zone_id = 1
        hour = 10
        employee_usage = {'Alice': {'used': 0}, 'Bob': {'used': 1}}
        schedule = {}
        errors = []
        
        best_employee = find_best_employee(available_employees, zone_id, hour, employee_usage, schedule, errors)
        
        self.assertEqual(best_employee, 'Alice')

    def test_find_best_employee_already_assigned(self):
        available_employees = [('Alice', {}), ('Bob', {})]
        zone_id = 1
        hour = 10
        employee_usage = {'Alice': {'used': 0}, 'Bob': {'used': 0}}
        schedule = {'Alice': [(1, {})]}
        errors = []
        
        best_employee = find_best_employee(available_employees, zone_id, hour, employee_usage, schedule, errors)
        
        self.assertEqual(best_employee, 'Bob')
        self.assertEqual(len(errors), 1)

    def test_find_best_employee_no_skills(self):
        available_employees = [('Alice', {}), ('Bob', {})]
        zone_id = 2
        hour = 10 
        employee_usage = {'Alice': {'used': 0}, 'Bob': {'used': 0}}
        schedule = {}
        errors = []
        
        best_employee = find_best_employee(available_employees, zone_id, hour, employee_usage, schedule, errors)
        
        self.assertEqual(best_employee, None)

