from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.recommend, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('about/', views.about, name='about'),
    path('history/', views.history, name='history'),
    path('profile/', views.profile, name='profile'),
]
