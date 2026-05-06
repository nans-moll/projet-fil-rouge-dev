"""
Couche service (séparation responsabilités — SOLID).

Encapsule la logique métier de recherche/filtrage des biens
pour qu'elle reste testable et réutilisable hors des vues.
"""
from django.db.models import Q, QuerySet

from .models import Property


class PropertySearchService:
    """Service de recherche multi-critères."""

    DEFAULT_SORT = "-published_at"

    @staticmethod
    def search(filters: dict) -> QuerySet[Property]:
        qs = (
            Property.objects.filter(status=Property.Status.AVAILABLE)
            .select_related("agency", "agent")
            .prefetch_related("photos")
        )

        if query := filters.get("query"):
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(reference__icontains=query)
                | Q(city__icontains=query)
                | Q(postal_code__icontains=query)
            )

        if v := filters.get("transaction_type"):
            qs = qs.filter(transaction_type=v)
        if v := filters.get("property_type"):
            qs = qs.filter(property_type=v)
        if v := filters.get("city"):
            qs = qs.filter(city__icontains=v)
        if v := filters.get("min_price"):
            qs = qs.filter(price__gte=v)
        if v := filters.get("max_price"):
            qs = qs.filter(price__lte=v)
        if v := filters.get("min_surface"):
            qs = qs.filter(surface__gte=v)
        if v := filters.get("min_rooms"):
            qs = qs.filter(rooms__gte=v)
        if filters.get("has_garage"):
            qs = qs.filter(has_garage=True)
        if filters.get("has_garden"):
            qs = qs.filter(has_garden=True)
        if filters.get("has_pool"):
            qs = qs.filter(has_pool=True)

        sort = filters.get("sort") or PropertySearchService.DEFAULT_SORT
        return qs.order_by(sort)
