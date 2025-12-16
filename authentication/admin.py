from django.contrib import admin
from .models import CustomUser, Theme, JournalEntry, Tag, Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'journal_entry', 'type', 'timezone', 'next_run_at', 'is_active')
    list_filter = ('type', 'timezone', 'is_active', 'frequency')
    search_fields = ('journal_entry__title',)
    readonly_fields = ('created_at', 'updated_at', 'last_sent_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('journal_entry', 'type', 'timezone', 'is_active')
        }),
        ('One-time Settings', {
            'fields': ('run_at',),
            'classes': ('collapse',)
        }),
        ('Recurring Settings', {
            'fields': ('frequency', 'day_of_week', 'day_of_month', 'time_of_day'),
            'classes': ('collapse',)
        }),
        ('State', {
            'fields': ('next_run_at', 'last_sent_at', 'created_at', 'updated_at')
        }),
    )


# Register other models
admin.site.register(CustomUser)
admin.site.register(Theme)
admin.site.register(JournalEntry)
admin.site.register(Tag)
