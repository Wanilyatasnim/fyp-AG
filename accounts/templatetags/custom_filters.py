from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    """
    Checks if the user belongs to a group OR has a matching 'role' field.
    This ensures compatibility with the Claude UI snippet while respecting
    our existing role-based architecture.
    """
    if not user.is_authenticated:
        return False
        
    # Check the role field first (our primary system)
    if user.role.lower() == group_name.lower():
        return True
        
    # Fallback to Django Groups if any exist
    return user.groups.filter(name=group_name).exists()
