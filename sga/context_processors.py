from django.contrib.auth.models import User

from sga.backend.constants import SGA_DATETIME_FORMAT, EPOCH_FORMAT, Roles


def logged_in_user(request):
    # TODO: Add auth
    try:
        return {
            "user_name": request.user.get_full_name(),
            "role": request.role,
            "Roles": Roles
        }
    except:
        return {}

def datetime_formats(request):
    return {
        "SGA_DATETIME_FORMAT": SGA_DATETIME_FORMAT,
        "EPOCH_FORMAT": EPOCH_FORMAT
    }