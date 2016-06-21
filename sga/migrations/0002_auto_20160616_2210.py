# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-16 22:10
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import sga.backend.constants


class Migration(migrations.Migration):

    dependencies = [
        ('sga', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='graded',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='course',
            name='administrators',
            field=models.ManyToManyField(related_name='administrator_courses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='course',
            name='graders',
            field=models.ManyToManyField(related_name='grader_courses', through='sga.Grader', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='course',
            name='students',
            field=models.ManyToManyField(related_name='student_courses', through='sga.Student', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='submission',
            name='grade',
            field=models.IntegerField(null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='submission',
            name='graded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='graded_submissions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='submission',
            name='grader_document',
            field=models.FileField(null=True, upload_to=sga.backend.files.grader_submission_file_path),
        ),
        migrations.AlterField(
            model_name='submission',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submitted_submissions', to=settings.AUTH_USER_MODEL),
        ),
    ]
