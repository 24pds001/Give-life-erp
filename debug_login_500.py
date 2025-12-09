import os
import django
from django.test import Client
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_system.settings')
django.setup()

# Temporarily allow * in ALLOWED_HOSTS for test client if needed, 
# but Client usually bypasses this. 
# However, previous debug script modified settings. Let's just try Client.

client = Client()
try:
    response = client.get('/login/')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 500:
        # If it's a template error, it might be in context or content
        # But Client.get() usually doesn't print the full traceback unless we catch it?
        # Actually, Django test client suppresses exceptions by default but we can force it?
        # Or just print response.content if it's a debug page.
        pass
except Exception as e:
    import traceback
    traceback.print_exc()

# To get the exception to propagate:
from django.test.utils import setup_test_environment
setup_test_environment()
client = Client()
try:
    response = client.get('/login/')
    print(f"Status Code: {response.status_code}")
except Exception as e:
    import traceback
    traceback.print_exc()
