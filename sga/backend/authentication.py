# TODO: Implement real authentication

from django.contrib.auth.decorators import user_passes_test


def is_student(user):
    return user.is_student()

def is_grader(user):
    return user.username.startswith("grader")

def is_admin(user):
    return user.username.startswith("admin")

# The following are decorators
student_view = user_passes_test(is_student)
grader_view = user_passes_test(is_grader)
admin_view = user_passes_test(is_admin)