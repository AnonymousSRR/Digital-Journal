"""
Views for user authentication.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from .models import CustomUser, Theme, JournalEntry
from .forms import CustomUserCreationForm, CustomAuthenticationForm
import requests
import json
from django.db import models


@login_required
def my_journals_view(request):
    """
    View for displaying all journal entries for the current user.
    """
    # Get all journal entries for the current user, ordered by creation date (newest first)
    journal_entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        journal_entries = journal_entries.filter(
            models.Q(title__icontains=search_query) |
            models.Q(theme__name__icontains=search_query) |
            models.Q(answer__icontains=search_query)
        )
    
    return render(request, 'my_journals.html', {
        'journal_entries': journal_entries,
        'search_query': search_query
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
                answer=answer
            )
            
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
        
        print(f"Calling Cohere API for theme: {theme_name}")
        response = requests.post(COHERE_API_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        generated_prompt = result['generations'][0]['text'].strip()
        
        # Clean up the response
        if generated_prompt.startswith('"') and generated_prompt.endswith('"'):
            generated_prompt = generated_prompt[1:-1]
        
        print(f"Generated prompt: {generated_prompt}")
        return generated_prompt
        
    except requests.exceptions.RequestException as e:
        print(f"Cohere API error: {e}")
        # Fallback prompt if API fails - use a relevant example from the theme
        fallback_prompts = theme_examples.get(theme_name, [])
        if fallback_prompts:
            return fallback_prompts[0]  # Return the first example as fallback
        return f"Reflect on how {theme_name.lower()} has impacted your work or life recently. What insights can you draw from this experience?"
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Fallback prompt if any other error occurs
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
