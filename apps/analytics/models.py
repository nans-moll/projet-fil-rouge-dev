"""
Modèles analytiques.

`MarketSnapshot` : capture mensuelle de l'état du marché par ville/type
(générée par une commande management ou un job programmé).
Utilisé pour suivre les tendances dans le temps sans recalculer à chaque requête.
"""
from django.db import models

from apps.properties.models import TimestampedModel


class MarketSnapshot(TimestampedModel):
    """Snapshot mensuel des indicateurs marché par ville et type de bien."""

    period = models.DateField(help_text="Premier jour du mois concerné")
    city = models.CharField(max_length=100)
    property_type = models.CharField(max_length=15)
    transaction_type = models.CharField(max_length=10)

    listings_count = models.PositiveIntegerField(default=0)
    avg_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    median_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_price_per_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_surface = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    sales_count = models.PositiveIntegerField(default=0)
    avg_days_to_sell = models.DecimalField(max_digits=6, decimal_places=1, default=0)

    class Meta:
        verbose_name = "Snapshot marché"
        verbose_name_plural = "Snapshots marché"
        unique_together = [("period", "city", "property_type", "transaction_type")]
        ordering = ["-period", "city"]

    def __str__(self):
        return f"{self.period:%Y-%m} {self.city} {self.property_type}"
