from django.contrib import admin
from .models import CustomUser, Theme, JournalEntry, Tag

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Theme)
admin.site.register(JournalEntry)
admin.site.register(Tag)
