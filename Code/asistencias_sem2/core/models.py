from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    is_professor = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'core'

class Subject(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    semester = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    credits = models.PositiveIntegerField()
    group = models.CharField(max_length=10)
    professor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_professor': True})

    def __str__(self):
        return f"{self.name} ({self.code}) - Semestre {self.semester}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_code = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    institutional_email = models.EmailField(unique=True)
    photo = models.ImageField(upload_to='students_photos/')
    subjects = models.ManyToManyField(Subject, related_name='students', blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_code})"