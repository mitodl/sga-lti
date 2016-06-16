from django.contrib.auth.models import User

from sga.constants import SGA_DATETIME_FORMAT, EPOCH_FORMAT


def logged_in_user(request):
    # TODO: Add auth
    try:
        return {
            "user_name": "{last_name}, {first_name}".format(last_name=request.user.last_name, first_name=request.user.first_name)
        }
    except:
        return {}

def datetime_formats(request):
    return {
        "SGA_DATETIME_FORMAT": SGA_DATETIME_FORMAT,
        "EPOCH_FORMAT": EPOCH_FORMAT
    }