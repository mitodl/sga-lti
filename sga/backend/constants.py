import os


SGA_DATETIME_FORMAT = "l, F j, Y, g:iA e"
EPOCH_FORMAT = "U"

# Messages
GRADER_TO_STUDENT_CONFIRM = ("Are you sure you want to change this grader to a student? " +
                             "Students currently assigned to this grader will no longer " +
                             "be assigned to any grader.")
STUDENT_TO_GRADER_CONFIRM = "Are you sure you want to change this student into a grader?"
UNASSIGN_GRADER_CONFIRM = ("Are you sure you want to unassign the grader from this student? " +
                           "(You can reassign the same grader or a new grader after this action.)")
UNASSIGN_STUDENT_CONFIRM = ("Are you sure you want to unassign this student from this grader? " +
                           "(You can reassign the same grader or a new grader after this action.)")

VALID_FILE_UPLOAD_EXTENSIONS = [".pdf"]

class Roles():
    student = "student"
    grader = "grader"
    admin = "admin"

def student_submission_file_path(instance, filename):
    return "student-uploads/{course_id}/{last_name}_{first_name}-{assignment_name}{extension}".format(
        course_id=instance.assignment.course.edx_id,
        last_name=instance.student.last_name,
        first_name=instance.student.first_name,
        assignment_name=instance.assignment.name,
        extension=os.path.splitext(filename)[-1]
    )

def grader_submission_file_path(instance, filename):
    return "grader-uploads/{course_id}/{last_name}_{first_name}-{assignment_name}{extension}".format(
        course_id=instance.assignment.course.edx_id,
        last_name=instance.student.last_name,
        first_name=instance.student.first_name,
        assignment_name=instance.assignment.name,
        extension=os.path.splitext(filename)[-1]
    )
