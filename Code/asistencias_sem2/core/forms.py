from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Subject, Student

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    is_professor = forms.BooleanField(required=False, label='¿Es profesor?')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_professor']

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['code', 'name', 'semester', 'credits', 'group']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_code', 'first_name', 'last_name', 'institutional_email', 'photo']

class SubjectAssignmentForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all())
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())