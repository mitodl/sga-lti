import os


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
