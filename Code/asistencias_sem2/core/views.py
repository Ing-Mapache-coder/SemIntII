from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, SubjectForm, StudentForm, SubjectAssignmentForm
from .models import Subject, Student, User

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if form.cleaned_data.get('is_professor'):
                user.is_professor = True
            else:
                user.is_student = True
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')

@login_required
def create_subject(request):
    if not request.user.is_professor:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.professor = request.user
            subject.save()
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'core/create_subject.html', {'form': form})

@login_required
def subject_list(request):
    if request.user.is_professor:
        subjects = Subject.objects.filter(professor=request.user)
    else:
        student = Student.objects.get(user=request.user)
        subjects = student.subjects.all()
    return render(request, 'core/subject_list.html', {'subjects': subjects})

@login_required
def create_student(request):
    if not request.user.is_professor:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            # Crear usuario para el estudiante
            user = User.objects.create_user(
                username=form.cleaned_data['institutional_email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['institutional_email'],
                password=form.cleaned_data['student_code'],  # Contraseña temporal
                is_student=True
            )
            student.user = user
            student.save()
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'core/create_student.html', {'form': form})

@login_required
def student_list(request):
    if not request.user.is_professor:
        return redirect('dashboard')
    students = Student.objects.all()
    return render(request, 'core/student_list.html', {'students': students})

@login_required
def assign_subject(request):
    if not request.user.is_professor:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SubjectAssignmentForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            subject = form.cleaned_data['subject']
            student.subjects.add(subject)
            return redirect('subject_list')
    else:
        form = SubjectAssignmentForm()
    return render(request, 'core/assign_subject.html', {'form': form})

@login_required
def remove_student_from_subject(request, subject_id, student_id):
    if not request.user.is_professor:
        return redirect('dashboard')
    
    subject = Subject.objects.get(id=subject_id, professor=request.user)
    student = Student.objects.get(id=student_id)
    student.subjects.remove(subject)
    return redirect('subject_detail', subject_id=subject_id)

@login_required
def subject_detail(request, subject_id):
    subject = Subject.objects.get(id=subject_id)
    students = subject.students.all()
    return render(request, 'core/subject_detail.html', {
        'subject': subject,
        'students': students,
        'is_professor': request.user.is_professor
    })