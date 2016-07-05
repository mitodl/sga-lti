"""
Constant definitions
"""


# Datetime formats
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
UNSUBMIT_CONFIRM = "Are you sure you want to mark this submission as not submitted?"


INVALID_S3_CHARACTERS_REGEX = r"[^a-zA-Z0-9!\-_.*'()/]"
STUDIO_USER_USERNAME = "cuid:student"


class Roles():
    """
    Role definitions
    """
    student = "student"
    grader = "grader"
    admin = "admin"
    none = "none"
