from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "agency", "is_active")
    list_filter = ("role", "agency", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Métier Ymmo", {
            "fields": ("role", "agency", "phone", "avatar"),
        }),
        ("Coordonnées", {
            "fields": ("address", "city", "postal_code"),
            "classes": ("collapse",),
        }),
        ("Préférences de recherche", {
            "fields": ("search_min_price", "search_max_price", "search_city"),
            "classes": ("collapse",),
        }),
    )
