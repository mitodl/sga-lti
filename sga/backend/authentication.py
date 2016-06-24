"""
Authentication decorators
"""

from functools import wraps

from django.http import HttpResponseForbidden


def allowed_roles(allowed_roles_list):
    """
    Decorator for views that checks that the user has permission to access the
    view function. If the user's role (request.role, which is set by SGAMiddleware)
    is in allowed_roles_list, the view_function is called, otherwise it returns a
    403 response.
    """
    def decorator(view_func):
        """ Decorator """
        @wraps(view_func)
        def _wrapped_view(request, course_id, *args, **kwargs):
            """ Wrapped function """
            if request.session.course_roles[course_id] in allowed_roles_list:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden()
        return _wrapped_view
    return decorator
