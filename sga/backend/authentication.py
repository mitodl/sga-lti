from django.http import HttpResponseForbidden
from functools import wraps

from sga.backend.constants import Roles
from sga.models import Course


def is_student(request):
    course = get_course_from_session(request)
    return course.has_student(request.user)

def is_grader(request):
    course = get_course_from_session(request)
    return course.has_grader(request.user)

def is_admin(request):
    course = get_course_from_session(request)
    return course.has_admin(request.user)


ROLE_TO_FUNC = {
    Roles.student: is_student,
    Roles.grader: is_grader,
    Roles.admin: is_admin
}


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
            for role in allowed_roles_list:
                if ROLE_TO_FUNC[role](request):
                    request.role = role
                    return view_func(request, *args, **kwargs)
            return HttpResponseForbidden()
        return _wrapped_view
    return decorator


def get_course_from_session(request):
    try:
        return Course.objects.get(edx_id=request.session.get("context_id"))
    except:
        raise Exception("Please log in")


