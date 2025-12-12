
import os
import django
import sys

# Setup Django environment
sys.path.append(r'd:\N Cloud\OneDrive\M.Sc Data Science\Sem 4\Internship Project\Give Life Project\Give life erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_system.settings')
django.setup()

from core.models import RolePermission

def create_default_permissions():
    defaults = RolePermission.get_default_permissions()
    
    # helper to grant full access
    def grant_full(perms, modules):
        for m in modules:
            if m in perms:
                for action in perms[m]:
                    perms[m][action] = True
        return perms

    # helper to grant view only
    def grant_view(perms, modules):
        for m in modules:
            if m in perms:
                perms[m]['view'] = True
        return perms

    # 1. ADMIN - Implicitly handled by code logic, but good to have entry
    # Admin logic in model overrides this, but let's be consistent.
    
    # 2. SUPERVISOR - Full Access (legacy behavior)
    supervisor_perms = RolePermission.get_default_permissions()
    # Grant everything
    for m in supervisor_perms:
        for a in supervisor_perms[m]:
            supervisor_perms[m][a] = True
            
    RolePermission.objects.update_or_create(
        role='SUPERVISOR',
        defaults={'permissions': supervisor_perms, 'description': 'Full access to all modules.'}
    )
    print("Updated SUPERVISOR permissions.")

    # 3. ACCOUNTANT - Specific modules
    # ['billing', 'invoices', 'payroll', 'vendor_payments', 'purchases', 'worklogs', 'attendance']
    accountant_modules = ['sales_bill', 'outer_bill', 'inner_bill', 'vendors', 'purchases', 'vendor_payments', 'payroll', 'worklogs', 'attendance', 'reports']
    # Note: 'billing' spans sales/outer/inner bills. 'invoices' is somewhat redundant or specific view. 
    # Current models.py uses specific names. I should map legacy names to new schema if needed, but here I use new schema keys.
    
    accountant_perms = RolePermission.get_default_permissions()
    accountant_perms = grant_full(accountant_perms, accountant_modules)
    RolePermission.objects.update_or_create(
        role='ACCOUNTANT',
        defaults={'permissions': accountant_perms, 'description': 'Access to financial and operational modules.'}
    )
    print("Updated ACCOUNTANT permissions.")

    # 4. REGULAR EMPLOYEE - Billing/Invoices only (legacy: 'billing', 'invoices')
    employee_modules = ['sales_bill', 'outer_bill', 'inner_bill']
    employee_perms = RolePermission.get_default_permissions()
    # Assuming full access to billing for now as per legacy 'True'
    employee_perms = grant_full(employee_perms, employee_modules)
    RolePermission.objects.update_or_create(
        role='EMPLOYEE',
        defaults={'permissions': employee_perms, 'description': 'Access to billing modules.'}
    )
    print("Updated EMPLOYEE permissions.")

    # 5. STUDENT - specific logic in views often, but minimal module access by default?
    # Legacy code didn't explicitly give student access in has_module_access, so it defaulted to False.
    # We keep it as False (all empty).
    student_perms = RolePermission.get_default_permissions()
    RolePermission.objects.update_or_create(
        role='STUDENT',
        defaults={'permissions': student_perms, 'description': 'Limited access.'}
    )
    print("Updated STUDENT permissions.")

if __name__ == '__main__':
    create_default_permissions()
