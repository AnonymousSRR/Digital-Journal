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
    path('api/emotion-stats/', views.get_emotion_stats, name='emotion_stats'),
    path('api/emotion-trends/', views.get_emotion_trends, name='emotion_trends'),
    path('api/emotion-by-theme/', views.get_emotion_by_theme, name='emotion_by_theme'),
    path('api/entries-by-emotion/', views.get_entries_by_emotion, name='get_entries_by_emotion'),
] 