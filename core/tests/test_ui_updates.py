import os
import django
from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

import sys
# Go up 3 levels: core/tests/test_ui_updates.py -> core/tests -> core -> root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_system.settings')
from django.conf import settings
if not settings.configured:
    django.setup()
    settings.ALLOWED_HOSTS += ['testserver']
else:
    django.setup()
    # If already configured, we might need to patch it or just hope it works if we modify it?
    # Modifying settings at runtime is tricky. Better to use @override_settings decorator or just modify the list if it's a list.
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')

from core.views import dashboard, billing_home

def test_dashboard_access():
    print("Testing Dashboard Access...")
    User = get_user_model()
    # Create a test user if not exists
    user, created = User.objects.get_or_create(username='test_admin', role='ADMIN')
    if created:
        user.set_password('password')
        user.save()

    client = Client()
    client.force_login(user)
    
    response = client.get(reverse('dashboard'))
    if response.status_code == 200:
        print("SUCCESS: Dashboard loaded (200 OK)")
        # Check for merged button text
        if b'Billing & Invoices' in response.content:
            print("SUCCESS: 'Billing & Invoices' button found")
        else:
            print("FAILURE: 'Billing & Invoices' button NOT found")
    else:
        print(f"FAILURE: Dashboard returned {response.status_code}")

def test_billing_home_access():
    print("\nTesting Billing Home Access...")
    User = get_user_model()
    user = User.objects.get(username='test_admin')
    
    client = Client()
    client.force_login(user)
    
    response = client.get(reverse('billing_home'))
    if response.status_code == 200:
        print("SUCCESS: Billing Home loaded (200 OK)")
        # Check for table headers
        if b'Recent Invoices' in response.content:
            print("SUCCESS: 'Recent Invoices' table found")
        else:
            print("FAILURE: 'Recent Invoices' table NOT found")
            
        # Check for filter form
        if b'name="bill_type"' in response.content:
            print("SUCCESS: Filter form found")
        else:
            print("FAILURE: Filter form NOT found")
            print("Response content snippet:", response.content[:500]) # Print first 500 chars
            if b'<form' in response.content:
                 print("Form tag found")
            else:
                 print("Form tag NOT found")
    else:
        print(f"FAILURE: Billing Home returned {response.status_code}")

if __name__ == "__main__":
    try:
        test_dashboard_access()
        test_billing_home_access()
    except Exception as e:
        print(f"ERROR: {e}")
