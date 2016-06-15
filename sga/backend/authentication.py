from django.http import HttpResponseForbidden
from functools import wraps
from sga.models import Course


def user_has_permission(test_func):
    """
    Decorator for views that checks that the user has permission to access the
    view function, returning a 403 response if the user does not. The test
    should be a callable that takes the request object and returns True if the
    user has permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from pprint import pprint
            pprint(request)
            if test_func(request):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden()
        return _wrapped_view
    return decorator


def get_course_from_session(request):
    course, created = Course.objects.get_or_create(edx_id=request.session.get("context_id"))
    return course


def is_student(request):
    course = get_course_from_session(request)
    return course.has_student(request.user)

def is_grader(request):
    course = get_course_from_session(request)
    return course.has_grader(request.user)

def is_admin(request):
    course = get_course_from_session(request)
    return course.has_admin(request.user)


# View decorators
student_view = user_has_permission(is_student)
grader_view = user_has_permission(is_grader)
admin_view = user_has_permission(is_admin)