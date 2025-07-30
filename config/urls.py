"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from authentication import views

@login_required
def home_view(request):
    """Home view for authenticated users."""
    return render(request, 'home.html')

def home_redirect(request):
    """Redirect to authentication page for unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('authentication:auth')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home_redirect'),
    path('home/', home_view, name='home'),
    path('home/theme-selector/', views.theme_selector_view, name='theme_selector'),
    path('home/answer-prompt/', views.answer_prompt_view, name='answer_prompt'),
    path('home/my-journals/', views.my_journals_view, name='my_journals'),
    path('home/delete-journal/<int:entry_id>/', views.delete_journal_entry, name='delete_journal_entry'),
    path('home/toggle-bookmark/<int:entry_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('login/', include('authentication.urls')),
]

# Add static files serving for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
