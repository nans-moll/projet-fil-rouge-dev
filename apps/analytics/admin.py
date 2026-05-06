from django.contrib import admin
from .models import MarketSnapshot


@admin.register(MarketSnapshot)
class MarketSnapshotAdmin(admin.ModelAdmin):
    list_display = ("period", "city", "property_type", "transaction_type",
                    "listings_count", "avg_price", "median_price")
    list_filter = ("property_type", "transaction_type", "period")
    search_fields = ("city",)
