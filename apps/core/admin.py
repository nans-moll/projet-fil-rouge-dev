from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "subject", "is_processed", "created_at")
    list_filter = ("is_processed", "created_at")
    search_fields = ("full_name", "email", "subject", "message")
    list_editable = ("is_processed",)
    readonly_fields = ("created_at",)
