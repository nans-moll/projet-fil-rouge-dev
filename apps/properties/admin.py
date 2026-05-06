from django.contrib import admin
from .models import Agency, FavoriteProperty, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_headquarters", "phone", "active_properties_count")
    list_filter = ("is_headquarters", "region")
    search_fields = ("name", "city", "postal_code")
    prepopulated_fields = {"slug": ("name", "city")}


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "title", "city", "property_type",
        "transaction_type", "price", "status", "agency", "is_featured",
    )
    list_filter = ("status", "property_type", "transaction_type", "is_featured", "agency", "city")
    search_fields = ("reference", "title", "description", "city", "postal_code")
    list_editable = ("status", "is_featured")
    readonly_fields = ("views_count", "created_at", "updated_at")
    inlines = [PropertyImageInline]
    fieldsets = (
        ("Identification", {"fields": ("reference", "title", "slug", "description")}),
        ("Classification", {"fields": ("property_type", "transaction_type", "status", "is_featured")}),
        ("Caractéristiques", {"fields": (
            "surface", "land_surface", "rooms", "bedrooms", "bathrooms", "floor",
            "has_garage", "has_garden", "has_pool", "has_balcony", "has_elevator",
            "is_furnished", "energy_class", "construction_year",
        )}),
        ("Prix", {"fields": ("price", "monthly_charges", "agency_fees_percent")}),
        ("Localisation", {"fields": ("address", "city", "postal_code", "region",
                                     "latitude", "longitude")}),
        ("Liens", {"fields": ("agency", "agent", "seller")}),
        ("Stats", {"fields": ("views_count", "published_at", "created_at", "updated_at")}),
    )


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "is_main", "order", "created_at")
    list_filter = ("is_main",)


@admin.register(FavoriteProperty)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "property", "created_at")
