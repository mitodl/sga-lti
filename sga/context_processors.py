from django.contrib.auth.models import User


def logged_in_user(request):
    # TODO: Add auth
    try:
        return {
            "user_name": "{last_name}, {first_name}".format(last_name=request.user.last_name, first_name=request.user.first_name)
        }
    except:
        return {}