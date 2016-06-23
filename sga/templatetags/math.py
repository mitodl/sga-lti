"""
Custom math templatetags
"""

from django import template

register = template.Library()


@register.filter
def subtract(value, arg):
    """
    Subtracts the arg from the value
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return value - arg
        except Exception:  # pylint: disable=broad-except
            return ""
