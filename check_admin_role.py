import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_system.settings')
django.setup()

from core.models import User

try:
    admin_user = User.objects.get(username='admin')
    print(f"User: {admin_user.username}")
    print(f"Role: {admin_user.role}")
    print(f"Is Superuser: {admin_user.is_superuser}")
    
    if admin_user.role != 'ADMIN':
        print("Updating role to ADMIN...")
        admin_user.role = 'ADMIN'
        admin_user.save()
        print("Role updated.")
except User.DoesNotExist:
    print("User 'admin' not found.")
