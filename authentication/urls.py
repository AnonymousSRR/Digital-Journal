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
    
    # Version history URLs
    path('entry/<int:entry_id>/versions/', views.entry_version_history, name='entry_version_history'),
    path('entry/<int:entry_id>/version/<int:version_number>/', views.view_version, name='view_version'),
    path('entry/<int:entry_id>/compare/', views.compare_versions, name='compare_versions'),
    path('entry/<int:entry_id>/version/<int:version_number>/restore/', views.restore_version, name='restore_version'),
    path('entry/<int:entry_id>/version/<int:version_number>/export-pdf/', views.export_version_pdf, name='export_version_pdf'),
    path('entry/<int:entry_id>/compare-pdf/', views.export_version_comparison_pdf, name='export_version_comparison_pdf'),
    path('api/entry/<int:entry_id>/versions/', views.api_version_timeline, name='api_version_timeline'),
    path('api/entry/<int:entry_id>/diff/', views.api_version_diff, name='api_version_diff'),
    path('api/entry/<int:entry_id>/version/<int:version_number>/restore/', views.api_restore_version, name='api_restore_version'),
    path('api/entry/<int:entry_id>/version/<int:version_number>/export-pdf/', views.api_export_version_pdf, name='api_export_version_pdf'),
] 