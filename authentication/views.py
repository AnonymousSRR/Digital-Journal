"""
Views for user authentication.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from .models import CustomUser, Theme, JournalEntry, Tag
from .forms import CustomUserCreationForm, CustomAuthenticationForm
import requests
import json
import time
from datetime import datetime
from django.db import models
from django.utils.text import slugify


@login_required
def my_journals_view(request):
    """
    View for displaying all journal entries for the current user.
    """
    # Get all journal entries for the current user
    journal_entries = JournalEntry.objects.filter(user=request.user)
    
    # Handle visibility filter
    visibility_filter = request.GET.get('visibility', 'all')
    if visibility_filter == 'private':
        journal_entries = journal_entries.filter(visibility='private')
    elif visibility_filter == 'shared':
        journal_entries = journal_entries.filter(visibility='shared')
    # 'all' shows everything (no filter)
    
    # Handle tag filter
    selected_tag = request.GET.get('tag')
    if selected_tag:
        journal_entries = journal_entries.filter(tags__slug=selected_tag)
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        journal_entries = journal_entries.filter(
            models.Q(title__icontains=search_query) |
            models.Q(theme__name__icontains=search_query) |
            models.Q(answer__icontains=search_query)
        )
    
    # Separate bookmarked and regular entries
    bookmarked_entries = journal_entries.filter(bookmarked=True).order_by('-created_at')
    regular_entries = journal_entries.filter(bookmarked=False).order_by('-created_at')
    
    # Build user tag list with counts for the sidebar/filter
    user_tags = (
        Tag.objects.filter(user=request.user)
           .annotate(entry_count=models.Count('entries'))
           .order_by('name')
    )
    
    return render(request, 'my_journals.html', {
        'bookmarked_entries': bookmarked_entries,
        'regular_entries': regular_entries,
        'search_query': search_query,
        'visibility_filter': visibility_filter,
        'tags': user_tags,
        'selected_tag': selected_tag,
    })

@login_required
def delete_journal_entry(request, entry_id):
    """Delete a journal entry"""
    if request.method == 'POST':
        # Get the journal entry and ensure it belongs to the current user
        journal_entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
        
        # Delete the entry
        journal_entry.delete()
        
        # Show success message
        messages.success(request, 'Journal entry deleted successfully.')
        
        # Redirect back to my journals page
        return redirect('my_journals')
    
    # If not POST request, redirect to my journals
    return redirect('my_journals')


@login_required
def theme_selector_view(request):
    """
    View for theme selection page.
    """
    themes = Theme.objects.all().order_by('name')
    return render(request, 'theme_selector.html', {
        'themes': themes
    })


@login_required
def answer_prompt_view(request):
    """
    View for displaying the generated prompt based on selected theme.
    """
    theme_id = request.GET.get('theme_id')
    print(f"Answer prompt view called with theme_id: {theme_id}")
    
    if not theme_id:
        print("No theme_id provided")
        messages.error(request, 'No theme selected. Please select a theme first.')
        return redirect('authentication:theme_selector')
    
    try:
        theme = Theme.objects.get(id=theme_id)
        print(f"Found theme: {theme.name}")
    except Theme.DoesNotExist:
        print(f"Theme with id {theme_id} not found")
        messages.error(request, 'Selected theme not found.')
        return redirect('authentication:theme_selector')
    
    if request.method == 'POST':
        answer = request.POST.get('answer')
        title = request.POST.get('title')
        prompt = request.POST.get('prompt')
        writing_time = request.POST.get('writing_time', 0)
        visibility = request.POST.get('visibility', 'private')
        tags_raw = request.POST.get('tags', '')
        
        # Validate visibility value
        if visibility not in ['private', 'shared']:
            visibility = 'private'
        
        if not answer or not title:
            messages.error(request, 'Please provide both a title and your response.')
            return render(request, 'answer_prompt.html', {
                'theme': theme,
                'prompt': prompt,
                'answer': answer,
                'title': title
            })
        
        try:
            # Create the journal entry with the prompt from the form
            journal_entry = JournalEntry.objects.create(
                user=request.user,
                theme=theme,
                title=title,
                prompt=prompt,
                answer=answer,
                bookmarked=False,  # Add default value for deployed app
                writing_time=int(writing_time) if writing_time else 0,
                visibility=visibility
            )
            
            # Process and attach tags
            tags = []
            for name in [t.strip() for t in tags_raw.split(',') if t.strip()]:
                slug = slugify(name)
                if slug:  # Only process if slug is not empty
                    tag, _ = Tag.objects.get_or_create(
                        user=request.user,
                        slug=slug,
                        defaults={'name': name}
                    )
                    tags.append(tag)
            if tags:
                journal_entry.tags.add(*tags)
            
            messages.success(request, f'Journal entry "{title}" saved successfully!')
            return redirect('home')
            
        except Exception as e:
            print(f"Error saving journal entry: {e}")
            messages.error(request, 'Error saving journal entry. Please try again.')
            return render(request, 'answer_prompt.html', {
                'theme': theme,
                'prompt': prompt,
                'answer': answer,
                'title': title
            })
    
    # Generate dynamic prompt using Cohere API for GET requests
    prompt = generate_theme_prompt(theme.name, theme.description)
    print(f"Generated prompt: {prompt}")
    
    return render(request, 'answer_prompt.html', {
        'theme': theme,
        'prompt': prompt
    })


def generate_theme_prompt(theme_name, theme_description):
    """
    Generate a dynamic prompt using Cohere API based on the theme.
    """
    COHERE_API_KEY = 'yyvejL50thRkw70IRXctuFKyrkBwJ0QUBYBt6nEn'
    COHERE_API_URL = 'https://api.cohere.ai/v1/generate'
    
    # Theme-specific examples to guide the AI
    theme_examples = {
        'Technology Impact': [
            'How do I balance short-term delivery pressures with long-term technical health?',
            'Are we investing enough in automated testing and continuous delivery?',
            'How am I helping engineers develop skills that will sustain technical excellence?'
        ],
        'Delivery Impact': [
            'What\'s one recent delivery mistake we made, and how can we ensure it doesn\'t happen again?',
            'When have I felt pressure to compromise on quality or take shortcuts? How did I respond?',
            'How can I foster predictability in delivery without adding stress?'
        ],
        'Business Impact': [
            'How do I ensure that stakeholders see engineering as a strategic partner rather than a service function?',
            'What\'s one business metric I should pay more attention to as a tech leader?',
            'Have I effectively explained the ROI of a technical initiative to a stakeholder?'
        ],
        'Team Impact': [
            'How well do I adjust my leadership style based on the situation and individual?',
            'Have I created a space where people feel safe to speak up and challenge ideas?',
            'What\'s one strength in a team member I should actively help them develop?'
        ],
        'Org Impact': [
            'How have I contributed beyond my immediate role in the organization?',
            'What\'s one improvement I could propose that would benefit multiple teams?',
            'Am I actively advocating for a strong engineering culture that attracts the right people?'
        ]
    }
    
    # Get examples for the current theme
    examples = theme_examples.get(theme_name, [])
    examples_text = '\n'.join([f'• {example}' for example in examples])
    
    # Create the prompt for Cohere
    system_prompt = f"""
    You are a helpful assistant that generates journal prompts for tech leaders and engineering managers.
    
    Based on the theme "{theme_name}" and its description "{theme_description or 'No description provided'}", 
    generate a short, concise question that encourages reflection and journaling.
    
    Here are example prompts for this theme to guide your style and approach:
    {examples_text}
    
    IMPORTANT: Do NOT copy or repeat any of the example prompts above. Generate a NEW, UNIQUE question that follows the same style and approach but is completely different from the examples.
    
    Requirements:
    - Keep the prompt short and to the point (one sentence)
    - Make it a single question that starts with "How", "What", "When", "Have I", or "Am I"
    - Focus on personal reflection and insights relevant to tech leadership
    - Be specific and actionable
    - Use clear, engaging language
    - Avoid generic questions - make them specific to the theme
    - Follow the style and tone of the examples provided
    - Create a completely NEW question, not a variation of the examples
    
    Generate only the question, nothing else.
    """
    
    # Retry configuration
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            headers = {
                'Authorization': f'Bearer {COHERE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'command',
                'prompt': system_prompt,
                'max_tokens': 100,
                'temperature': 0.7,
                'k': 0,
                'stop_sequences': [],
                'return_likelihoods': 'NONE'
            }
            
            print(f"Calling Cohere API for theme: {theme_name} (attempt {attempt + 1}/{max_retries})")
            
            # Increase timeout for each retry attempt
            timeout = 10 + (attempt * 5)  # 10s, 15s, 20s
            
            response = requests.post(
                COHERE_API_URL, 
                headers=headers, 
                json=data, 
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generated_prompt = result['generations'][0]['text'].strip()
            
            # Clean up the response
            if generated_prompt.startswith('"') and generated_prompt.endswith('"'):
                generated_prompt = generated_prompt[1:-1]
            
            print(f"Generated prompt: {generated_prompt}")
            return generated_prompt
            
        except requests.exceptions.Timeout as e:
            print(f"Cohere API timeout error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries reached. Using fallback prompt.")
                break
                
        except requests.exceptions.ConnectionError as e:
            print(f"Cohere API connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries reached. Using fallback prompt.")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Cohere API request error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries reached. Using fallback prompt.")
                break
                
        except (KeyError, IndexError, ValueError) as e:
            print(f"Cohere API response parsing error: {e}")
            # Don't retry for parsing errors as they indicate malformed response
            break
            
        except Exception as e:
            print(f"Unexpected error during Cohere API call: {e}")
            # Don't retry for unexpected errors
            break
    
    # Fallback logic - use a relevant example from the theme
    print("Using fallback prompt due to API errors")
    fallback_prompts = theme_examples.get(theme_name, [])
    if fallback_prompts:
        return fallback_prompts[0]  # Return the first example as fallback
    return f"Reflect on how {theme_name.lower()} has impacted your work or life recently. What insights can you draw from this experience?"


class SignUpView(CreateView):
    """
    View for user registration.
    """
    form_class = CustomUserCreationForm
    template_name = 'authentication/signup.html'
    success_url = reverse_lazy('authentication:signin')
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        """
        user = form.save()
        messages.success(
            self.request,
            f'Account created successfully for {user.get_full_name()}. Please sign in.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Handle form validation errors.
        """
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        """
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'signup'
        return context


class SignInView(FormView):
    """
    View for user login.
    """
    form_class = CustomAuthenticationForm
    template_name = 'authentication/signin.html'
    success_url = reverse_lazy('home')  # Redirect to home after login
    
    def form_valid(self, form):
        """
        Handle successful login.
        """
        email = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=email, password=password)
        
        if user is not None:
            login(self.request, user)
            messages.success(
                self.request,
                f'Welcome back, {user.get_full_name()}!'
            )
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Invalid email or password.')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Handle form validation errors.
        """
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        """
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'signin'
        return context


class AuthenticationView(FormView):
    """
    Combined view for both signin and signup with tab switching.
    """
    form_class = CustomAuthenticationForm
    template_name = 'authentication/auth.html'
    success_url = reverse_lazy('home')
    
    def get_form_class(self):
        """
        Return the appropriate form class based on the active tab.
        """
        active_tab = self._get_active_tab()
        if active_tab == 'signup':
            return CustomUserCreationForm
        return CustomAuthenticationForm
    
    def _get_active_tab(self):
        """
        Get the active tab from GET or POST data.
        """
        if self.request.method == 'POST':
            # Check the form action URL for tab information
            form_action = self.request.POST.get('form_action', '')
            if 'tab=signup' in form_action:
                return 'signup'
            return 'signin'
        return self.request.GET.get('tab', 'signin')
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        """
        active_tab = self._get_active_tab()
        
        if active_tab == 'signup':
            return self._handle_signup(form)
        else:
            return self._handle_signin(form)
    
    def _handle_signup(self, form):
        """
        Handle signup form submission.
        """
        try:
            user = form.save()
            messages.success(
                self.request,
                f'Account created successfully for {user.get_full_name()}. Please sign in.'
            )
            return HttpResponseRedirect(reverse_lazy('authentication:auth') + '?tab=signin')
        except Exception as e:
            messages.error(self.request, f'Error creating account: {str(e)}')
            return self.form_invalid(form)
    
    def _handle_signin(self, form):
        """
        Handle signin form submission.
        """
        email = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=email, password=password)
        
        if user is not None:
            login(self.request, user)
            messages.success(
                self.request,
                f'Welcome back, {user.get_full_name()}!'
            )
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Invalid email or password.')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Handle form validation errors.
        """
        # Get form errors and display them
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        """
        context = super().get_context_data(**kwargs)
        active_tab = self._get_active_tab()
        context['active_tab'] = active_tab
        context['signin_form'] = CustomAuthenticationForm() if active_tab == 'signin' else None
        context['signup_form'] = CustomUserCreationForm() if active_tab == 'signup' else None
        return context


@login_required
def logout_view(request):
    """
    View for user logout.
    """
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('authentication:auth')

@login_required
def toggle_bookmark(request, entry_id):
    """Toggle bookmark status of a journal entry"""
    if request.method == 'POST':
        # Get the journal entry and ensure it belongs to the current user
        journal_entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
        
        # Toggle the bookmark status
        journal_entry.bookmarked = not journal_entry.bookmarked
        journal_entry.save()
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'bookmarked': journal_entry.bookmarked,
                'message': 'Entry bookmarked successfully.' if journal_entry.bookmarked else 'Bookmark removed successfully.'
            })
        
        # Show success message for regular requests
        messages.success(request, 'Entry bookmarked successfully.' if journal_entry.bookmarked else 'Bookmark removed successfully.')
        
        # Redirect back to my journals page
        return redirect('my_journals')
    
    # If not POST request, redirect to my journals
    return redirect('my_journals')


@login_required
def toggle_visibility(request, entry_id):
    """Toggle visibility status of a journal entry between private and shared"""
    if request.method == 'POST':
        # Get the journal entry and ensure it belongs to the current user
        journal_entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
        
        # Toggle the visibility status
        journal_entry.visibility = 'shared' if journal_entry.visibility == 'private' else 'private'
        journal_entry.save()
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'visibility': journal_entry.visibility,
                'message': f'Entry marked as {journal_entry.get_visibility_display()}.'
            })
        
        # Show success message for regular requests
        messages.success(request, f'Entry visibility changed to {journal_entry.get_visibility_display()}.')
        
        # Redirect back to my journals page
        return redirect('my_journals')
    
    # If not POST request, redirect to my journals
    return redirect('my_journals')


# Emotion Analytics Views

@login_required
def get_emotion_stats(request):
    """
    Get overall emotion statistics for the logged-in user.
    Returns JSON with:
    - total_entries: number of entries
    - primary_emotion_distribution: dict of emotion counts
    - average_sentiment_score: float
    - visibility_breakdown: dict of visibility counts
    """
    from django.db.models import Avg
    
    entries = JournalEntry.objects.filter(user=request.user)
    
    # Count emotion distribution
    emotion_distribution = {}
    for entry in entries:
        emotion = entry.primary_emotion
        emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
    
    # Calculate average sentiment
    avg_sentiment = entries.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0.0
    
    # Add visibility breakdown
    visibility_stats = {
        'private': entries.filter(visibility='private').count(),
        'shared': entries.filter(visibility='shared').count()
    }
    
    stats = {
        'total_entries': entries.count(),
        'primary_emotion_distribution': emotion_distribution,
        'average_sentiment_score': round(avg_sentiment, 3),
        'visibility_breakdown': visibility_stats
    }
    
    return JsonResponse(stats)


@login_required
def get_emotion_trends(request):
    """
    Get emotion trends over time for the logged-in user.
    Query params: days (default 30) - number of days to look back
    Returns JSON array of daily emotion data
    """
    from datetime import datetime, timedelta
    from django.db.models import Avg
    
    days = int(request.GET.get('days', 30))
    start_date = datetime.now().date() - timedelta(days=days)
    
    entries = JournalEntry.objects.filter(
        user=request.user,
        created_at__date__gte=start_date
    ).order_by('created_at')
    
    # Group emotions by date
    trends = {}
    for entry in entries:
        date_key = entry.created_at.date().isoformat()
        if date_key not in trends:
            trends[date_key] = {'date': date_key, 'emotions': {}, 'average_sentiment': 0.0}
        
        emotion = entry.primary_emotion
        trends[date_key]['emotions'][emotion] = trends[date_key]['emotions'].get(emotion, 0) + 1
    
    # Calculate average sentiment per date
    for date_key in trends.keys():
        date_entries = entries.filter(created_at__date=date_key)
        avg_sentiment = date_entries.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0.0
        trends[date_key]['average_sentiment'] = round(avg_sentiment, 3)
    
    return JsonResponse(list(trends.values()), safe=False)


@login_required
def get_emotion_by_theme(request):
    """
    Get emotion statistics broken down by theme.
    Returns JSON object with theme names as keys
    """
    entries = JournalEntry.objects.filter(user=request.user)
    
    theme_emotions = {}
    for entry in entries:
        theme_name = entry.theme.name
        if theme_name not in theme_emotions:
            theme_emotions[theme_name] = {
                'emotions': {},
                'sentiments': [],
                'count': 0
            }
        
        emotion = entry.primary_emotion
        theme_emotions[theme_name]['emotions'][emotion] = \
            theme_emotions[theme_name]['emotions'].get(emotion, 0) + 1
        theme_emotions[theme_name]['sentiments'].append(entry.sentiment_score)
        theme_emotions[theme_name]['count'] += 1
    
    # Format response
    result = {}
    for theme_name, data in theme_emotions.items():
        avg_sentiment = sum(data['sentiments']) / len(data['sentiments']) if data['sentiments'] else 0.0
        result[theme_name] = {
            'emotion_distribution': data['emotions'],
            'average_sentiment': round(avg_sentiment, 3),
            'entry_count': data['count']
        }
    
    return JsonResponse(result)


@login_required
def get_entries_by_emotion(request):
    """
    Get journal entries filtered by emotion and optional sentiment range.
    Query params:
    - emotion: primary emotion to filter by
    - min_sentiment: minimum sentiment score (-1.0 to 1.0)
    - max_sentiment: maximum sentiment score (-1.0 to 1.0)
    Returns JSON with entries array and count
    """
    from authentication.serializers import serialize_journal_entry_emotion
    
    emotion = request.GET.get('emotion')
    min_sentiment = request.GET.get('min_sentiment')
    max_sentiment = request.GET.get('max_sentiment')
    
    entries = JournalEntry.objects.filter(user=request.user)
    
    if emotion:
        entries = entries.filter(primary_emotion=emotion)
    
    if min_sentiment:
        try:
            entries = entries.filter(sentiment_score__gte=float(min_sentiment))
        except ValueError:
            pass
    
    if max_sentiment:
        try:
            entries = entries.filter(sentiment_score__lte=float(max_sentiment))
        except ValueError:
            pass
    
    serialized_entries = [serialize_journal_entry_emotion(entry) for entry in entries]
    return JsonResponse({'entries': serialized_entries, 'count': entries.count()})


@login_required
def emotion_analytics(request):
    """View for displaying emotion analytics dashboard."""
    context = {
        'page_title': 'Emotional Analytics'
    }
    return render(request, 'authentication/emotion_analytics.html', context)


@login_required
def export_emotion_report_csv(request):
    """Export emotion data as CSV file."""
    from authentication.utils import EmotionReportGenerator
    
    days = int(request.GET.get('days', 90))
    csv_content = EmotionReportGenerator.generate_csv_report(request.user, days=days)
    
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="emotion_report_{datetime.now().date()}.csv"'
    return response


@login_required
def export_emotion_report_json(request):
    """Export emotion data and statistics as JSON."""
    from authentication.utils import EmotionReportGenerator
    from datetime import datetime
    
    days = int(request.GET.get('days', 90))
    stats = EmotionReportGenerator.generate_summary_stats(request.user, days=days)
    return JsonResponse(stats)


# Version History Views

@login_required
def entry_version_history(request, entry_id):
    """
    Display timeline of all versions for a journal entry.
    Shows version list with metadata and links to view/compare/restore.
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    versions = entry.versions.all().order_by('-version_number')
    
    context = {
        'entry': entry,
        'versions': versions,
        'page_title': f'Version History - {entry.title}'
    }
    return render(request, 'authentication/entry_version_history.html', context)


@login_required
def view_version(request, entry_id, version_number):
    """
    Display a specific version of a journal entry.
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    version = get_object_or_404(entry.versions, version_number=version_number)
    
    # Check if this is the current version
    is_current = version.is_current()
    
    context = {
        'entry': entry,
        'version': version,
        'is_current': is_current,
        'page_title': f'{entry.title} - Version {version_number}'
    }
    return render(request, 'authentication/view_version.html', context)


@login_required
def compare_versions(request, entry_id):
    """
    Compare two versions of a journal entry side-by-side.
    Query params: v1=version_number, v2=version_number
    """
    from difflib import unified_diff
    
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    v1_num = request.GET.get('v1')
    v2_num = request.GET.get('v2')
    
    if not v1_num or not v2_num:
        messages.error(request, 'Please select two versions to compare.')
        return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    try:
        v1 = get_object_or_404(entry.versions, version_number=int(v1_num))
        v2 = get_object_or_404(entry.versions, version_number=int(v2_num))
    except (ValueError, Exception):
        messages.error(request, 'One or both versions not found.')
        return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    # Generate text diff for answer field
    v1_lines = v1.answer.splitlines(keepends=True)
    v2_lines = v2.answer.splitlines(keepends=True)
    diff_lines = list(unified_diff(v1_lines, v2_lines, lineterm=''))
    
    # Prepare comparison data
    comparison = {
        'v1': v1,
        'v2': v2,
        'title_changed': v1.title != v2.title,
        'prompt_changed': v1.prompt != v2.prompt,
        'answer_changed': v1.answer != v2.answer,
        'diff': diff_lines,
    }
    
    context = {
        'entry': entry,
        'comparison': comparison,
        'page_title': f'Compare Versions {v1_num} & {v2_num}'
    }
    return render(request, 'authentication/compare_versions.html', context)


@login_required
def api_version_timeline(request, entry_id):
    """
    API endpoint: Get JSON timeline of all versions for an entry.
    Response: [
        {
            'version_number': 3,
            'created_at': '2025-01-15T10:30:00Z',
            'created_by': 'user@example.com',
            'change_summary': 'Title updated',
            'title': 'Entry Title',
            'is_current': true
        },
        ...
    ]
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    versions = entry.versions.all().order_by('-version_number')
    
    data = [
        {
            'version_number': v.version_number,
            'created_at': v.created_at.isoformat(),
            'created_by': v.created_by.email if v.created_by else 'System',
            'change_summary': v.change_summary,
            'title': v.title,
            'is_current': v.is_current()
        }
        for v in versions
    ]
    
    return JsonResponse({'versions': data, 'entry_id': entry_id})


@login_required
def api_version_diff(request, entry_id):
    """
    API endpoint: Get unified diff between two versions.
    Query params: v1=version_number, v2=version_number
    Response: {
        'v1': {...version_data...},
        'v2': {...version_data...},
        'diff': [...diff_lines...],
        'title_changed': bool,
        'answer_changed': bool
    }
    """
    from difflib import unified_diff
    
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    v1_num = request.GET.get('v1')
    v2_num = request.GET.get('v2')
    
    if not v1_num or not v2_num:
        return JsonResponse({'error': 'Missing v1 or v2 parameter'}, status=400)
    
    try:
        v1 = get_object_or_404(entry.versions, version_number=int(v1_num))
        v2 = get_object_or_404(entry.versions, version_number=int(v2_num))
    except ValueError:
        return JsonResponse({'error': 'Invalid version number'}, status=400)
    
    # Generate diff
    v1_lines = v1.answer.splitlines(keepends=True)
    v2_lines = v2.answer.splitlines(keepends=True)
    diff_lines = list(unified_diff(v1_lines, v2_lines, lineterm=''))
    
    data = {
        'v1': {'version_number': v1.version_number, 'title': v1.title, 'created_at': v1.created_at.isoformat()},
        'v2': {'version_number': v2.version_number, 'title': v2.title, 'created_at': v2.created_at.isoformat()},
        'diff': diff_lines,
        'title_changed': v1.title != v2.title,
        'answer_changed': v1.answer != v2.answer,
        'prompt_changed': v1.prompt != v2.prompt
    }
    
    return JsonResponse(data)


@login_required
def restore_version(request, entry_id, version_number):
    """
    Restore a journal entry to a previous version.
    Creates a new version with the content from the specified version.
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    source_version = get_object_or_404(entry.versions, version_number=version_number)
    
    if request.method == 'POST':
        try:
            # Update entry with content from source version
            entry.title = source_version.title
            entry.answer = source_version.answer
            entry.prompt = source_version.prompt
            entry.theme = source_version.theme
            entry.visibility = source_version.visibility
            entry.save()
            
            # Update the newly created version to mark it as a restore
            latest_version = entry.get_current_version()
            latest_version.edit_source = 'restore'
            latest_version.restored_from_version = version_number
            latest_version.change_summary = f'Restored from version {version_number}'
            latest_version.save()
            
            messages.success(
                request,
                f'Entry restored to version {version_number} successfully. '
                f'A new version has been created.'
            )
            return redirect('authentication:entry_version_history', entry_id=entry_id)
        
        except Exception as e:
            messages.error(request, f'Error restoring version: {str(e)}')
            return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    # GET request: show confirmation page
    context = {
        'entry': entry,
        'source_version': source_version,
        'page_title': f'Restore to Version {version_number}?'
    }
    return render(request, 'authentication/confirm_restore_version.html', context)


@login_required
def api_restore_version(request, entry_id, version_number):
    """
    API endpoint: Restore version (POST request).
    Response: {'success': true, 'new_version_number': N, 'message': '...'}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    source_version = get_object_or_404(entry.versions, version_number=version_number)
    
    try:
        # Restore content
        entry.title = source_version.title
        entry.answer = source_version.answer
        entry.prompt = source_version.prompt
        entry.theme = source_version.theme
        entry.visibility = source_version.visibility
        entry.save()
        
        # Mark the new version as restore
        latest_version = entry.get_current_version()
        latest_version.edit_source = 'restore'
        latest_version.restored_from_version = version_number
        latest_version.change_summary = f'Restored from version {version_number}'
        latest_version.save()
        
        return JsonResponse({
            'success': True,
            'new_version_number': latest_version.version_number,
            'message': f'Version {version_number} restored successfully.'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def export_version_pdf(request, entry_id, version_number):
    """
    Export a specific version as PDF.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from io import BytesIO
    
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    version = get_object_or_404(entry.versions, version_number=version_number)
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title and metadata
    story.append(Paragraph(f"<b>{version.title}</b>", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    # Version info
    metadata = f"""
    <b>Entry ID:</b> {entry.id}<br/>
    <b>Version:</b> {version.version_number} of {entry.version_count()}<br/>
    <b>Created:</b> {version.created_at.strftime('%B %d, %Y at %I:%M %p')}<br/>
    <b>Theme:</b> {version.theme.name if version.theme else 'N/A'}<br/>
    <b>Visibility:</b> {version.get_visibility_display()}<br/>
    <b>Edit Source:</b> {version.get_edit_source_display()}
    """
    story.append(Paragraph(metadata, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Prompt section
    if version.prompt:
        story.append(Paragraph("<b>Prompt:</b>", styles['Heading3']))
        story.append(Paragraph(version.prompt, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Answer section
    story.append(Paragraph("<b>Response:</b>", styles['Heading3']))
    story.append(Paragraph(version.answer, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer with export info
    footer = f"<i>Exported on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>"
    story.append(Paragraph(footer, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return as response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"{slugify(version.title)}_v{version.version_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_version_comparison_pdf(request, entry_id):
    """
    Export a comparison of two versions as PDF.
    Query params: v1=version_number, v2=version_number
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from io import BytesIO
    
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    v1_num = request.GET.get('v1')
    v2_num = request.GET.get('v2')
    
    if not v1_num or not v2_num:
        messages.error(request, 'Please specify v1 and v2 query parameters.')
        return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    try:
        v1 = get_object_or_404(entry.versions, version_number=int(v1_num))
        v2 = get_object_or_404(entry.versions, version_number=int(v2_num))
    except ValueError:
        messages.error(request, 'Invalid version number.')
        return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(f"<b>Version Comparison: {entry.title}</b>", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    # Comparison summary
    summary = f"""
    <b>Comparing Version {v1.version_number} vs Version {v2.version_number}</b><br/>
    <b>Title Changed:</b> {'Yes' if v1.title != v2.title else 'No'}<br/>
    <b>Content Changed:</b> {'Yes' if v1.answer != v2.answer else 'No'}
    """
    story.append(Paragraph(summary, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Version 1 section
    story.append(Paragraph(f"<b>Version {v1.version_number}</b> ({v1.created_at.strftime('%b %d, %Y')})", styles['Heading3']))
    story.append(Paragraph(f"Title: {v1.title}", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(v1.answer, styles['Normal']))
    story.append(PageBreak())
    
    # Version 2 section
    story.append(Paragraph(f"<b>Version {v2.version_number}</b> ({v2.created_at.strftime('%b %d, %Y')})", styles['Heading3']))
    story.append(Paragraph(f"Title: {v2.title}", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(v2.answer, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer = f"<i>Exported on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>"
    story.append(Paragraph(footer, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return as response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"{slugify(entry.title)}_v{v1.version_number}_vs_v{v2.version_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def api_export_version_pdf(request, entry_id, version_number):
    """
    API endpoint: Export version as PDF (returns file stream).
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from io import BytesIO
    
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    version = get_object_or_404(entry.versions, version_number=version_number)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"<b>{version.title}</b>", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    metadata = f"<b>Version {version.version_number}</b> | {version.created_at.strftime('%B %d, %Y')}"
    story.append(Paragraph(metadata, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(version.answer, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"{slugify(version.title)}_v{version.version_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
