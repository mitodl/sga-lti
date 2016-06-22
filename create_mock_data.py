"""
Contains a function for creating mock data
"""

from datetime import datetime

from sga.models import Course, Assignment, Grader, Student, User


def create_mock_data():
    """ Function for creating mock data """
    admin_user = User.objects.create(
        first_name="Admin",
        last_name="User",
        username="admin"
    )
    course = Course.objects.create(
        edx_id="courseid",
        name="Course Name"
    )
    course.administrators.add(admin_user)
    grader_user_1 = User.objects.create(
        first_name="Grader 1",
        last_name="User",
        username="grader1"
    )
    grader_user_2 = User.objects.create(
        first_name="Grader 2",
        last_name="User",
        username="grader2"
    )
    grader_1 = Grader.objects.create(
        max_students=3,
        user=grader_user_1,
        course=course
    )
    grader_2 = Grader.objects.create(
        max_students=1,
        user=grader_user_2,
        course=course
    )
    student_user_1 = User.objects.create(
        first_name="Student1",
        last_name="User",
        username="student1",
        email="student1@test"
    )
    student_user_2 = User.objects.create(
        first_name="Student2",
        last_name="User",
        username="student2",
        email="student2@test"
    )
    student_user_3 = User.objects.create(
        first_name="Student3",
        last_name="User",
        username="student3",
        email="student3@test"
    )
    student_user_4 = User.objects.create(
        first_name="Student4",
        last_name="User",
        username="student4",
        email="student4@test"
    )
    Student.objects.create(
        user=student_user_1,
        course=course,
        grader=grader_1
    )
    Student.objects.create(
        user=student_user_2,
        course=course,
        grader=grader_1
    )
    Student.objects.create(
        user=student_user_3,
        course=course,
        grader=grader_2
    )
    Student.objects.create(
        user=student_user_4,
        course=course
    )
    Assignment.objects.create(
        edx_id="assignment1id",
        name="Assignment 1 Name",
        due_date=datetime.utcnow(),
        grace_period=1,
        course=course
    )
    Assignment.objects.create(
        edx_id="assignment2id",
        name="Assignment 2 Name",
        due_date=datetime.utcnow(),
        grace_period=1,
        course=course
    )
    for user in User.objects.all():
        user.set_password(" ")
        user.save()
