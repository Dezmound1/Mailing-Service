from django.contrib import admin

from .models import MailingRecord


@admin.register(MailingRecord)
class MailingRecordAdmin(admin.ModelAdmin):
    """Admin configuration for MailingRecord."""

    list_display = ("external_id", "email", "subject", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("external_id", "email", "subject")
    readonly_fields = ("external_id", "email", "subject", "status", "created_at")
