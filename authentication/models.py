"""
Custom user model for the journal application.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model.
    Provides methods for creating users and superusers.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model that uses email as the primary identifier.
    """
    username = None  # Disable username field
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name='Email address',
        help_text='Your email address will be used as your username'
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name='First name',
        help_text='Enter your first name'
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name='Last name',
        help_text='Enter your last name'
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    show_quick_add_fab = models.BooleanField(
        default=False,
        help_text="Show the Quick Add FAB button on the home page"
    )
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'custom_user'
    
    def __str__(self):
        """
        Return a string representation of the user.
        """
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        """
        Return the full name of the user.
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """
        Return the short name of the user.
        """
        return self.first_name
    
    def clean(self):
        """
        Validate the user data.
        """
        super().clean()
        if self.email:
            self.email = self.email.lower()
    
    def save(self, *args, **kwargs):
        """
        Save the user with cleaned data.
        """
        self.clean()
        super().save(*args, **kwargs)


class Theme(models.Model):
    """
    Theme model for journal entries.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Tag model for categorizing journal entries.
    Each tag is user-scoped to maintain privacy.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=60)

    class Meta:
        unique_together = ('user', 'slug')
        indexes = [
            models.Index(fields=['user', 'slug']),
            models.Index(fields=['user', 'name']),
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class JournalEntry(models.Model):
    """
    Journal entry model for user journal entries.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    theme = models.ForeignKey(Theme, on_delete=models.PROTECT)
    prompt = models.TextField()  # dynamically generated prompt
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    bookmarked = models.BooleanField(default=False)  # New field for bookmarking
    writing_time = models.IntegerField(default=0, help_text="Time spent writing in seconds")
    
    # Visibility control field
    visibility = models.CharField(
        max_length=10,
        default='private',
        choices=[
            ('private', 'Private'),
            ('shared', 'Shared'),
        ],
        help_text="Control who can view this entry"
    )
    
    # Emotion analysis fields
    primary_emotion = models.CharField(
        max_length=20,
        default='neutral',
        choices=[
            ('joyful', 'Joyful'),
            ('sad', 'Sad'),
            ('angry', 'Angry'),
            ('anxious', 'Anxious'),
            ('calm', 'Calm'),
            ('neutral', 'Neutral'),
        ],
        help_text="Primary emotion detected in the entry"
    )
    sentiment_score = models.FloatField(
        default=0.0,
        help_text="Sentiment score from -1.0 (negative) to 1.0 (positive)"
    )
    emotion_data = models.JSONField(
        default=dict,
        help_text="Breakdown of emotions: {emotion: score}"
    )
    
    # Many-to-many relationship with tags
    tags = models.ManyToManyField('Tag', related_name='entries', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.created_at.date()} - {self.theme.name}"
    
    def is_private(self):
        """Check if this entry is private."""
        return self.visibility == 'private'
    
    def is_shared(self):
        """Check if this entry is shared."""
        return self.visibility == 'shared'
    
    def get_current_version(self):
        """Get the latest version of this entry."""
        return self.versions.latest('version_number')
    
    def get_version(self, version_number):
        """Get a specific version by number."""
        return self.versions.get(version_number=version_number)
    
    def version_count(self):
        """Get total number of versions."""
        return self.versions.count()


class JournalEntryVersion(models.Model):
    """
    Stores version snapshots of journal entries for history tracking.
    Each edit creates a new version record with full content snapshot.
    """
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    
    # Snapshot of entry content at this version
    title = models.CharField(max_length=200)
    answer = models.TextField()
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True)
    prompt = models.TextField()
    visibility = models.CharField(
        max_length=10,
        choices=[('private', 'Private'), ('shared', 'Shared')],
        default='private'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_versions')
    
    # Change tracking
    change_summary = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable description of what changed (e.g., 'Title and answer updated')"
    )
    
    # Track what triggered this version
    edit_source = models.CharField(
        max_length=20,
        choices=[
            ('initial', 'Initial Creation'),
            ('edit', 'Manual Edit'),
            ('restore', 'Restored from Version'),
        ],
        default='initial'
    )
    restored_from_version = models.IntegerField(
        null=True,
        blank=True,
        help_text="If edit_source='restore', the version number that was restored"
    )
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ('entry', 'version_number')
        indexes = [
            models.Index(fields=['entry', '-version_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.entry.title} - v{self.version_number}"
    
    def is_original(self):
        """Check if this is the original version (v1)."""
        return self.version_number == 1
    
    def is_current(self):
        """Check if this is the current/latest version."""
        return self.version_number == self.entry.versions.latest('version_number').version_number


class Reminder(models.Model):
    """
    Reminder model for journal entries supporting one-time and recurring reminders.
    """
    ONE_TIME = 'one_time'
    RECURRING = 'recurring'
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    TYPE_CHOICES = [
        (ONE_TIME, 'One-time'),
        (RECURRING, 'Recurring'),
    ]

    journal_entry = models.ForeignKey('JournalEntry', on_delete=models.CASCADE, related_name='reminders')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=ONE_TIME)
    timezone = models.CharField(max_length=50, default='UTC')

    # One-time
    run_at = models.DateTimeField(null=True, blank=True)

    # Recurring
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, null=True, blank=True)
    day_of_week = models.IntegerField(null=True, blank=True)  # 0-6 Monday-Sunday
    day_of_month = models.IntegerField(null=True, blank=True)  # 1-31
    time_of_day = models.TimeField(null=True, blank=True)

    # State
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'next_run_at']),
        ]

    def __str__(self):
        return f"Reminder<{self.id}> for entry {self.journal_entry_id}"


class AnalyticsEvent(models.Model):
    """
    Track user interaction analytics for features like quick-add modal.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='analytics_events')
    event_type = models.CharField(max_length=100, help_text="Type of event (e.g., 'quick_add_fab_clicked')")
    event_data = models.JSONField(default=dict, help_text="Additional event data")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'event_type', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} by {self.user.email} at {self.timestamp}"
