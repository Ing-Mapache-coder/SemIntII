from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Materias
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/create/', views.create_subject, name='create_subject'),
    path('subjects/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    
    # Estudiantes
    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.create_student, name='create_student'),
    
    # Asignación
    path('assign/', views.assign_subject, name='assign_subject'),
    path('subjects/<int:subject_id>/remove/<int:student_id>/', views.remove_student_from_subject, name='remove_student'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)