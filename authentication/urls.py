"""
URL configuration for authentication app.
"""
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('', views.AuthenticationView.as_view(), name='auth'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('signin/', views.SignInView.as_view(), name='signin'),
    path('logout/', views.logout_view, name='logout'),
] 