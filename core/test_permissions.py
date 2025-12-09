from django.test import TestCase, Client
from django.urls import reverse
from core.models import User

class GranularPermissionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(username='admin', password='password', role='ADMIN')
        self.employee_user = User.objects.create_user(username='employee', password='password', role='EMPLOYEE')
        self.billing_url = reverse('billing_home')
        self.manage_permissions_url = reverse('manage_user_permissions', args=[self.employee_user.pk])

    def test_employee_billing_access(self):
        # Login as employee
        self.client.login(username='employee', password='password')
        
        # Try to access billing - should fail (redirect to dashboard with error or just redirect)
        # Note: My view redirects to dashboard if unauthorized, or login if not logged in.
        # But wait, billing_home uses @user_passes_test which redirects to login URL if false.
        # So it should redirect to /login/?next=/billing/
        
        response = self.client.get(self.billing_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302) # Redirects
        
        # Grant billing permission
        self.employee_user.module_permissions = {'billing': True}
        self.employee_user.save()
        
        # Try again
        response = self.client.get(self.billing_url)
        self.assertEqual(response.status_code, 200)

    def test_admin_manage_permissions(self):
        # Login as admin
        self.client.login(username='admin', password='password')
        
        # Access management page
        response = self.client.get(self.manage_permissions_url)
        self.assertEqual(response.status_code, 200)
        
        # Grant permission via POST
        response = self.client.post(self.manage_permissions_url, {
            'billing': 'on',
            'inventory': 'on'
        })
        self.assertEqual(response.status_code, 302) # Redirects to user_list
        
        # Verify permissions updated
        self.employee_user.refresh_from_db()
        self.assertTrue(self.employee_user.module_permissions.get('billing'))
        self.assertTrue(self.employee_user.module_permissions.get('inventory'))
        self.assertFalse(self.employee_user.module_permissions.get('user_management', False))

    def test_default_role_permissions(self):
        # Supervisor should have access by default
        supervisor = User.objects.create_user(username='supervisor', password='password', role='SUPERVISOR')
        self.assertTrue(supervisor.has_module_access('billing'))
        self.assertTrue(supervisor.has_module_access('inventory'))
        
        # Accountant should have billing but not inventory (unless specified in model logic)
        accountant = User.objects.create_user(username='accountant', password='password', role='ACCOUNTANT')
        self.assertTrue(accountant.has_module_access('billing'))
        # Check model logic for accountant inventory access... 
        # In model: ACCOUNTANT gets 'billing', 'invoices', 'payroll', 'reports', 'purchases', 'vendor_payments', 'worklogs', 'attendance'
        self.assertFalse(accountant.has_module_access('inventory')) 
