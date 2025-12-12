from django import template

register = template.Library()

@register.filter
def has_module_access(user, module_name):
    if not user.is_authenticated:
        return False
    if hasattr(user, 'has_module_access'):
        return user.has_module_access(module_name)
    return False

@register.simple_tag
def has_bill_permission(user, bill, action='view'):
    if not user.is_authenticated:
        return False
    
    # Map bill type to module name
    module_map = {
        'INNER': 'inner_bill',
        'OUTER': 'outer_bill',
        'SALES': 'sales_bill'
    }
    module_name = module_map.get(bill.bill_type)
    if not module_name:
        return False
        
    # Check permission using the user method
    if hasattr(user, 'has_module_access'):
        has_perm = user.has_module_access(module_name, action)
        if has_perm:
            return True
            
        # Legacy/Creator fallback
        if action == 'edit' or action == 'delete':
             if bill.created_by == user:
                 return True
                 
    return False
