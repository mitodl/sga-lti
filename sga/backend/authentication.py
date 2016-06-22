"""
Authentication decorators
"""

from functools import wraps

from django.http import HttpResponseForbidden


def allowed_roles(allowed_roles_list):
    """
    Decorator for views that checks that the user has permission to access the
    view function, returning a 403 response if the user does not. The test
    should be a callable that takes the request object and returns True if the
    user has permission.
    """
    def decorator(view_func):
        """ Decorator """
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            """ Wrapped function """
            if request.role in allowed_roles_list:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden()
        return _wrapped_view
    return decorator
