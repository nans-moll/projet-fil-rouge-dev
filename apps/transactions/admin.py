from django.contrib import admin
from .models import InfoRequest, Transaction, TransactionStep, VisitRequest


@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = ("property", "full_name", "preferred_date", "status", "created_at")
    list_filter = ("status", "preferred_date")
    search_fields = ("full_name", "email", "property__reference")
    list_editable = ("status",)


@admin.register(InfoRequest)
class InfoRequestAdmin(admin.ModelAdmin):
    list_display = ("property", "full_name", "answered_at", "created_at")
    search_fields = ("full_name", "email", "question")


class TransactionStepInline(admin.TabularInline):
    model = TransactionStep
    extra = 0


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("reference", "property", "buyer", "agent", "status", "offer_price", "created_at")
    list_filter = ("status", "type")
    search_fields = ("reference", "property__reference", "buyer__last_name")
    inlines = [TransactionStepInline]


@admin.register(TransactionStep)
class TransactionStepAdmin(admin.ModelAdmin):
    list_display = ("transaction", "title", "is_completed", "visible_to_client", "created_at")
    list_filter = ("is_completed", "visible_to_client")
