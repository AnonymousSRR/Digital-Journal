# Journal Entry Reminders Implementation Plan

## Overview
Add one-time and recurring reminders for journal entries with timezone-aware scheduling. Store next-run state, display upcoming reminders in the UI, and automatically mark reminders as sent or expired via a management command. Include migrations to backfill existing entries with a "no reminder" default.

## Architecture
Django models hold reminder configuration and state per journal entry. A periodic job (management command invoked by cron/Heroku Scheduler) computes due reminders using timezone-aware datetimes and recurrence rules, sends notifications via existing services (or placeholder), and updates state. Views/serializers expose upcoming reminders for a user's entries. Templates render upcoming reminders. Migrations initialize defaults.

## Implementation Phases

### Phase 1: Data Model & Migrations
**Files**: `authentication/models.py`, `authentication/migrations/`, `config/settings.py`  
**Test Files**: `authentication/tests.py`, `tests/test_journal_app.py`

Add `Reminder` model linked to `JournalEntry` (assuming entries live in `authentication` or related app — follow existing journal entry model location), with fields for one-time or recurring configuration, timezone, and state tracking.

**Key code changes:**
```python
# authentication/models.py
from django.db import models
from django.utils import timezone

class Reminder(models.Model):
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
    day_of_month = models.IntegerField(null=True, blank=True) # 1-31
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
```

Backfill migration sets default "no reminder" by creating zero reminders for existing entries (implicit). Ensure timezone settings in `config/settings.py` support aware datetimes (`USE_TZ=True`).

**Test cases for this phase:**

- Test case 1: Create one-time reminder stores `run_at` and computes `next_run_at`

  ```python
  def test_create_one_time_reminder_defaults():
      entry = make_entry()  # factory/helper in tests
      rem = Reminder.objects.create(journal_entry=entry, type=Reminder.ONE_TIME, run_at=timezone.now())
      assert rem.run_at is not None
      assert rem.next_run_at is None or rem.next_run_at == rem.run_at
  ```

- Test case 2: Create recurring reminder with daily frequency

  ```python
  def test_create_recurring_daily_reminder():
      entry = make_entry()
      rem = Reminder.objects.create(
          journal_entry=entry,
          type=Reminder.RECURRING,
          frequency='daily',
          time_of_day=datetime.time(9, 0),
          timezone='America/Los_Angeles',
      )
      assert rem.frequency == 'daily'
  ```

**Technical details and Assumptions (if any):**
- `JournalEntry` model exists; adjust import path accordingly.
- Use `pytz`/`zoneinfo` (Python 3.9+) for timezone conversions.
- Backfill simply ensures existing entries have no reminders; no explicit per-entry record needed.

### Phase 2: Scheduling Logic (next-run computation)
**Files**: `authentication/services.py`, `authentication/utils.py`, `authentication/tests.py`  
**Test Files**: `tests/test_time_formatting.py`, `tests/test_journal_app.py`

Implement helper to compute `next_run_at` for one-time and recurring reminders using the stored timezone and recurrence rules.

**Key code changes:**
```python
# authentication/services.py
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class ReminderScheduler:
    def compute_next_run(self, reminder: Reminder, now: datetime | None = None) -> datetime | None:
        tz = ZoneInfo(reminder.timezone or 'UTC')
        now = (now or timezone.now()).astimezone(tz)
        if reminder.type == Reminder.ONE_TIME:
            if reminder.run_at:
                run = reminder.run_at.astimezone(tz)
                return run if run > now else None
            return None
        # Recurring
        tod = reminder.time_of_day or datetime.time(9, 0)
        base = now.replace(hour=tod.hour, minute=tod.minute, second=0, microsecond=0)
        if reminder.frequency == 'daily':
            candidate = base
            if candidate <= now:
                candidate = candidate + timedelta(days=1)
            return candidate
        if reminder.frequency == 'weekly':
            target_dow = reminder.day_of_week if reminder.day_of_week is not None else 0
            days_ahead = (target_dow - now.weekday()) % 7
            candidate = base + timedelta(days=days_ahead)
            if candidate <= now:
                candidate = candidate + timedelta(days=7)
            return candidate
        if reminder.frequency == 'monthly':
            dom = reminder.day_of_month or 1
            month = now.month
            year = now.year
            # move to this month dom
            try:
                candidate = now.replace(day=dom, hour=tod.hour, minute=tod.minute, second=0, microsecond=0)
            except ValueError:
                # handle invalid dom (e.g., Feb 30) – push to next valid month
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                candidate = now.replace(year=year, month=month, day=1, hour=tod.hour, minute=tod.minute, second=0, microsecond=0)
            if candidate <= now:
                # next month
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                candidate = candidate.replace(year=year, month=month)
            return candidate
        return None
```

**Test cases for this phase:**

- Test case 1: Daily reminder sets next run to tomorrow if past time

  ```python
  def test_daily_next_run_tomorrow_when_past():
      now = datetime(2025, 12, 16, 10, 0, tzinfo=ZoneInfo('UTC'))
      rem = make_daily_reminder(time_of_day=datetime.time(9, 0), timezone='UTC')
      nxt = ReminderScheduler().compute_next_run(rem, now=now)
      assert nxt.date() == (now.date() + timedelta(days=1))
  ```

- Test case 2: Weekly reminder computes next correct weekday

  ```python
  def test_weekly_next_run_target_weekday():
      now = datetime(2025, 12, 16, 10, 0, tzinfo=ZoneInfo('UTC'))  # Tuesday
      rem = make_weekly_reminder(day_of_week=2, time_of_day=datetime.time(9, 0), timezone='UTC')  # Wednesday
      nxt = ReminderScheduler().compute_next_run(rem, now=now)
      assert nxt.weekday() == 2
  ```

**Technical details and Assumptions:**
- Use `zoneinfo.ZoneInfo` rather than `pytz` where possible.
- Edge cases handled for invalid monthly day; prefer first of next month fallback.

### Phase 3: Management Command to Process Reminders
**Files**: `authentication/management/commands/process_reminders.py`, `authentication/services.py`  
**Test Files**: `authentication/tests.py`, `tests/test_journal_app.py`

Create command that:
- Finds active reminders with `next_run_at <= now` in their timezone.
- Sends notification (placeholder function; integrate with existing notification/email service if present).
- Updates `last_sent_at`, computes next `next_run_at` for recurring; deactivates one-time reminders after send; marks expired when `next_run_at` becomes `None`.

**Key code changes:**
```python
# authentication/management/commands/process_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone

class Command(BaseCommand):
    help = 'Process due journal entry reminders'

    def handle(self, *args, **options):
        now = timezone.now()
        due = Reminder.objects.filter(is_active=True, next_run_at__isnull=False, next_run_at__lte=now)
        count = 0
        scheduler = ReminderScheduler()
        for rem in due.select_related('journal_entry'):
            send_reminder(rem)  # implement in services
            rem.last_sent_at = now
            if rem.type == Reminder.ONE_TIME:
                rem.is_active = False
                rem.next_run_at = None
            else:
                rem.next_run_at = scheduler.compute_next_run(rem, now=now)
                if rem.next_run_at is None:
                    rem.is_active = False
            rem.save(update_fields=['last_sent_at', 'is_active', 'next_run_at'])
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Processed {count} reminders'))
```

**Test cases for this phase:**

- Test case 1: One-time reminders are sent and deactivated

  ```python
  def test_process_onetime_deactivates():
      rem = make_onetime_due_reminder()
      call_command('process_reminders')
      rem.refresh_from_db()
      assert rem.is_active is False
      assert rem.next_run_at is None
  ```

- Test case 2: Recurring reminder updates `next_run_at`

  ```python
  def test_process_recurring_updates_next_run():
      rem = make_daily_due_reminder()
      prev = rem.next_run_at
      call_command('process_reminders')
      rem.refresh_from_db()
      assert rem.next_run_at is not None and rem.next_run_at > prev
  ```

**Technical details and Assumptions:**
- Implement `send_reminder(reminder)` stub in `authentication/services.py`; integrate with actual notification later.
- Command scheduled via cron/Heroku Scheduler every 5 minutes.

### Phase 4: UI & API Exposure of Upcoming Reminders
**Files**: `authentication/serializers.py`, `authentication/views.py`, `templates/my_journals.html`, `templates/authentication/`  
**Test Files**: `tests/pages/`, `authentication/tests.py`

Expose upcoming reminders for a user to view alongside entries. Allow creating/updating reminder settings per entry.

**Key code changes:**
```python
# authentication/serializers.py
class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = [
            'id', 'type', 'timezone', 'run_at', 'frequency', 'day_of_week', 'day_of_month', 'time_of_day',
            'next_run_at', 'last_sent_at', 'is_active'
        ]

# authentication/views.py
class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Reminder.objects.filter(journal_entry__user=self.request.user)

    def perform_create(self, serializer):
        reminder = serializer.save()
        reminder.next_run_at = ReminderScheduler().compute_next_run(reminder)
        reminder.save(update_fields=['next_run_at'])

    def perform_update(self, serializer):
        reminder = serializer.save()
        reminder.next_run_at = ReminderScheduler().compute_next_run(reminder)
        reminder.save(update_fields=['next_run_at'])
```

Update `urls.py` to route the viewset. Update `my_journals.html` to show upcoming reminders list (next 10). Add a simple form to configure reminders.

**Test cases for this phase:**

- Test case 1: API returns upcoming reminders for authenticated user

  ```python
  def test_api_upcoming_reminders_authenticated(client, user):
      client.force_login(user)
      # create reminders
      res = client.get('/api/reminders/')
      assert res.status_code == 200
  ```

- Test case 2: Saving reminder recomputes `next_run_at`

  ```python
  def test_update_recomputes_next_run(api_client, user, reminder):
      api_client.force_authenticate(user=user)
      res = api_client.patch(f'/api/reminders/{reminder.id}/', {'time_of_day': '10:00:00'})
      assert res.status_code == 200
      reminder.refresh_from_db()
      assert reminder.next_run_at is not None
  ```

**Technical details and Assumptions:**
- Use DRF if present; otherwise implement standard Django views with forms.
- Keep UI minimal: upcoming reminders section with entry link, next run time.

### Phase 5: Backfill Migration & Admin Integration
**Files**: `authentication/admin.py`, `authentication/migrations/`, `authentication/tests.py`  
**Test Files**: `authentication/tests.py`

Add migration to ensure existing entries remain without reminders—no-op but ensures defaults and indexes applied. Add admin model registration for `Reminder`.

**Key code changes:**
```python
# authentication/admin.py
@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'journal_entry', 'type', 'timezone', 'next_run_at', 'is_active')
    list_filter = ('type', 'timezone', 'is_active')
    search_fields = ('journal_entry__title',)
```

**Test cases for this phase:**

- Test case 1: Migration applies and leaves existing entries unchanged

  ```python
  def test_backfill_no_reminders():
      # prior entries exist
      migrate_forward()
      assert Reminder.objects.count() >= 0
  ```

- Test case 2: Admin lists reminders

  ```python
  def test_admin_reminder_registered(admin_client):
      res = admin_client.get('/admin/authentication/reminder/')
      assert res.status_code == 200
  ```

## Technical Considerations
- **Dependencies**: ✓ [Recommended] Use `zoneinfo` for timezone handling (Python 3.9+); if not available, add `backports.zoneinfo`.
- **Edge Cases**: Invalid monthly day; DST transitions; user changes timezone; deactivating reminders; deleting entries cascades to reminders.
- **Testing Strategy**: Unit tests per phase; mock `send_reminder`; time-freeze tests using `freezegun` ✓ [Recommended].
- **Performance**: Index on `is_active, next_run_at`; batch processing in command with `select_related`.
- **Security**: Authenticate API; ensure reminder access scoped to owner.

## Testing Notes
- Each phase includes targeted unit tests.
- Follow pytest patterns in the repo; place Django tests under app tests file and repo `tests/` when appropriate.
- Cover happy paths and edge cases (timezone shifts, expired reminders).

## Success Criteria
- [ ] Model supports one-time and recurring reminders with timezone
- [ ] `next_run_at` computed and updated correctly
- [ ] Management command processes due reminders and updates state
- [ ] UI exposes upcoming reminders and allows configuration
- [ ] Backfill migration runs cleanly without altering existing entries
