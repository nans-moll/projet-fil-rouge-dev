"""
Services analytiques.

Fournit les agrégations utilisées par les dashboards et exposées au notebook.
Reste une couche fine au-dessus de l'ORM ; le notebook Python fait l'analyse fine
via Pandas (cf. `notebooks/`).
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, F, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.properties.models import Property
from apps.transactions.models import Transaction


class MarketAnalyticsService:
    """Calculs d'indicateurs marché à la volée."""

    @staticmethod
    def overview() -> dict:
        """KPIs globaux pour le dashboard direction."""
        active_qs = Property.objects.filter(status=Property.Status.AVAILABLE)
        sold_qs = Property.objects.filter(status=Property.Status.SOLD)
        return {
            "total_properties": Property.objects.count(),
            "active_listings": active_qs.count(),
            "sold": sold_qs.count(),
            "avg_price_active": active_qs.aggregate(Avg("price"))["price__avg"] or 0,
            "avg_price_sold": sold_qs.aggregate(Avg("price"))["price__avg"] or 0,
            "total_views": Property.objects.aggregate(Sum("views_count"))["views_count__sum"] or 0,
            "transactions_count": Transaction.objects.count(),
            "signed_transactions": Transaction.objects.filter(
                status=Transaction.Status.SIGNED
            ).count(),
        }

    @staticmethod
    def top_cities(limit: int = 10) -> list[dict]:
        """Top villes par volume d'annonces."""
        return list(
            Property.objects.filter(status=Property.Status.AVAILABLE)
            .values("city")
            .annotate(
                count=Count("id"),
                avg_price=Avg("price"),
                avg_surface=Avg("surface"),
            )
            .order_by("-count")[:limit]
        )

    @staticmethod
    def by_property_type() -> list[dict]:
        return list(
            Property.objects.filter(status=Property.Status.AVAILABLE)
            .values("property_type")
            .annotate(count=Count("id"), avg_price=Avg("price"))
            .order_by("-count")
        )

    @staticmethod
    def transactions_per_month(months: int = 12) -> list[dict]:
        since = timezone.now() - timedelta(days=months * 31)
        return list(
            Transaction.objects.filter(created_at__gte=since)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"), total=Sum("offer_price"))
            .order_by("month")
        )

    @staticmethod
    def popular_properties(limit: int = 10):
        """Biens les plus consultés (proxy pour 'biens populaires')."""
        return (
            Property.objects.filter(status=Property.Status.AVAILABLE)
            .order_by("-views_count")[:limit]
        )
