from core.models import RolePermission, User

def fix_permissions():
    try:
        # Get or create RolePermission for STUDENT
        role_perm, created = RolePermission.objects.get_or_create(role='STUDENT')
        
        # Ensure 'inventory' is in permissions
        perms = role_perm.permissions or {}
        if 'inventory' not in perms:
            perms['inventory'] = {'view': True, 'create': True, 'edit': True}
        else:
            perms['inventory']['view'] = True
            perms['inventory']['create'] = True
            perms['inventory']['edit'] = True # Allow return
            
        role_perm.permissions = perms
        role_perm.save()
        print("Updated STUDENT permissions for inventory.")
        
        # Also check existing student users if they have overrides (unlikely but possible)
        for u in User.objects.filter(role='STUDENT'):
            if u.module_permissions and 'inventory' in u.module_permissions:
                print(f"User {u.username} has override: {u.module_permissions['inventory']}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    fix_permissions()
