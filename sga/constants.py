import os


SGA_DATETIME_FORMAT = "l, F j, Y, g:iA e"
EPOCH_FORMAT = "U"

# Messages
GRADER_TO_STUDENT_CONFIRM = ("Are you sure you want to change this grader to a student? " +
                             "Students currently assigned to this grader will no longer " +
                             "be assigned to any grader.")
STUDENT_TO_GRADER_CONFIRM = "Are you sure you want to change this student into a grader?"

class Roles():
    student = "student"
    grader = "grader"
    admin = "admin"

def student_submission_file_path(instance, filename):
    return "student-uploads/{last_name}_{first_name}-{assignment_name}{extension}".format(
        last_name=instance.student.last_name,
        first_name=instance.student.first_name,
        assignment_name=instance.assignment.name,
        extension=os.path.splitext(filename)[-1]
    )

def grader_submission_file_path(instance, filename):
    return "grader-uploads/{last_name}_{first_name}-{assignment_name}{extension}".format(
        last_name=instance.student.last_name,
        first_name=instance.student.first_name,
        assignment_name=instance.assignment.name,
        extension=os.path.splitext(filename)[-1]
    )
