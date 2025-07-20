from django.contrib import admin
from .models import CustomUser, Theme, JournalEntry

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Theme)
admin.site.register(JournalEntry)
