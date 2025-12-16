"""
Management command to process due journal entry reminders.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import Reminder
from authentication.services import ReminderScheduler, send_reminder


class Command(BaseCommand):
    help = 'Process due journal entry reminders'

    def handle(self, *args, **options):
        """Process all due reminders."""
        now = timezone.now()
        due = Reminder.objects.filter(
            is_active=True,
            next_run_at__isnull=False,
            next_run_at__lte=now
        ).select_related('journal_entry')
        
        count = 0
        scheduler = ReminderScheduler()
        
        for rem in due:
            # Send the reminder
            send_reminder(rem)
            
            # Update state
            rem.last_sent_at = now
            
            if rem.type == Reminder.ONE_TIME:
                # Deactivate one-time reminders after sending
                rem.is_active = False
                rem.next_run_at = None
            else:
                # Compute next run for recurring reminders
                rem.next_run_at = scheduler.compute_next_run(rem, now=now)
                if rem.next_run_at is None:
                    rem.is_active = False
            
            rem.save(update_fields=['last_sent_at', 'is_active', 'next_run_at'])
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Processed {count} reminder(s)')
        )
