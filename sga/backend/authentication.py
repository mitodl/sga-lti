from django.http import HttpResponseForbidden
from functools import wraps

from sga.backend.constants import Roles


def allowed_roles(allowed_roles_list):
    """
    Decorator for views that checks that the user has permission to access the
    view function, returning a 403 response if the user does not. The test
    should be a callable that takes the request object and returns True if the
    user has permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.role in allowed_roles_list:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden()
        return _wrapped_view
    return decorator
