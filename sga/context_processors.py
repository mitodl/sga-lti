"""
Injects context into all views
"""

from sga.backend.constants import SGA_DATETIME_FORMAT, EPOCH_FORMAT, Roles


def logged_in_user(request):
    """ Injects user data and roles """
    try:
        return {
            "user_name": request.user.get_full_name(),
            "role": request.role,
            "Roles": Roles
        }
    except AttributeError:
        return {}


def datetime_formats(request):  # pylint: disable=unused-argument
    """ Injects custom datetime formats """
    return {
        "SGA_DATETIME_FORMAT": SGA_DATETIME_FORMAT,
        "EPOCH_FORMAT": EPOCH_FORMAT
    }
