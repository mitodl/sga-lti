"""
Contains a management command for creating mock data
"""
from datetime import datetime
from django.core.management import BaseCommand

from sga.models import Course, Assignment, Grader, Student, User


class CreateMockDataCommand(BaseCommand):
    """
    Management command for creating mock data
    """
    help = "Creates mock data (Course, Users, Students, Graders, Administrator, Assignments"

    def handle(self, *args, **options):
        """
        Function for creating mock data
        """
        admin_user, _ = User.objects.get_or_create(
            username="_admin_user"
        )
        course, _ = Course.objects.get_or_create(
            edx_id="course-v1:MITx+B101+2015_T3"
        )
        course.administrators.add(admin_user)
        grader_user_1, _ = User.objects.get_or_create(
            username="_grader1"
        )
        grader_user_2, _ = User.objects.get_or_create(
            username="_grader2"
        )
        grader_1, _ = Grader.objects.get_or_create(
            max_students=3,
            user=grader_user_1,
            course=course
        )
        grader_2, _ = Grader.objects.get_or_create(
            max_students=1,
            user=grader_user_2,
            course=course
        )
        student_user_1, _ = User.objects.get_or_create(
            username="_student1",
            email="_student1@test"
        )
        student_user_2, _ = User.objects.get_or_create(
            username="_student2",
            email="_student2@test"
        )
        student_user_3, _ = User.objects.get_or_create(
            username="_student3",
            email="_student3@test"
        )
        student_user_4, _ = User.objects.get_or_create(
            username="_student4",
            email="_student4@test"
        )
        Student.objects.get_or_create(
            user=student_user_1,
            course=course,
            grader=grader_1
        )
        Student.objects.get_or_create(
            user=student_user_2,
            course=course,
            grader=grader_1
        )
        Student.objects.get_or_create(
            user=student_user_3,
            course=course,
            grader=grader_2
        )
        Student.objects.get_or_create(
            user=student_user_4,
            course=course
        )
        Assignment.objects.get_or_create(
            edx_id="_assignment1id",
            name="_Assignment 1 Name",
            due_date=datetime.utcnow(),
            course=course
        )
        Assignment.objects.get_or_create(
            edx_id="_assignment2id",
            name="_Assignment 2 Name",
            due_date=datetime.utcnow(),
            course=course
        )
        self.stdout.write(self.style.SUCCESS("Successfully created mock data."))
