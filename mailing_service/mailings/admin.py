from django.contrib import admin

from .models import MailingRecord


@admin.register(MailingRecord)
class MailingRecordAdmin(admin.ModelAdmin):
    list_display = ("external_id", "email", "subject", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("external_id", "email", "subject")
    readonly_fields = ("created_at", "updated_at")
