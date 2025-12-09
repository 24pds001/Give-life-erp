from django import template

register = template.Library()

@register.filter
def has_module_access(user, module_name):
    if not user.is_authenticated:
        return False
    if hasattr(user, 'has_module_access'):
        return user.has_module_access(module_name)
    return False
