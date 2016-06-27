"""
Authentication decorators
"""

from functools import wraps
from django.http import HttpResponseForbidden

from sga.backend.constants import Roles
from sga.models import Course


def allowed_roles(allowed_roles_list):
    """
    Decorator for views that checks that the user has permission to access the
    view function. If the user's role (request.session["course_roles"][course_id],
    set by SGAMiddleware) is in allowed_roles_list, the view_function is called,
    otherwise it returns a 403 response.
    """
    def decorator(view_func):
        """ Decorator """
        @wraps(view_func)
        def _wrapped_view(request, course_id, *args, **kwargs):
            """ Wrapped function """
            role = request.session.get("course_roles", {}).get(course_id)
            if role in allowed_roles_list:
                request.role = role
                request.course = Course.objects.get(id=course_id)
                return view_func(request, course_id, *args, **kwargs)
            return HttpResponseForbidden()
        return _wrapped_view
    return decorator


def get_role(user, course_id):
    """
    Returns the role a user has in a course given the course id
    """
    if user.administrator_courses.filter(id=course_id).count():
        return Roles.admin
    elif user.grader_courses.filter(id=course_id).count():
        return Roles.grader
    elif user.student_courses.filter(id=course_id).count():
        return Roles.student
    else:
        return Roles.none
