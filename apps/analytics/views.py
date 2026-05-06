"""Vues d'analytics — dashboard direction (admin/agent)."""
import json

from django.views.generic import TemplateView

from apps.accounts.decorators import AgentRequiredMixin

from .services import MarketAnalyticsService


class MarketDashboardView(AgentRequiredMixin, TemplateView):
    """Dashboard analytique : KPIs, top villes, répartitions, tendances."""

    template_name = "analytics/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        svc = MarketAnalyticsService

        ctx["overview"] = svc.overview()
        ctx["top_cities"] = svc.top_cities(10)
        ctx["by_type"] = svc.by_property_type()
        ctx["popular"] = svc.popular_properties(10)

        # Données pour Chart.js (sérialisées)
        monthly = svc.transactions_per_month(12)
        ctx["chart_months"] = json.dumps([
            m["month"].strftime("%Y-%m") if m["month"] else "" for m in monthly
        ])
        ctx["chart_counts"] = json.dumps([m["count"] for m in monthly])

        type_data = svc.by_property_type()
        ctx["chart_type_labels"] = json.dumps([d["property_type"] for d in type_data])
        ctx["chart_type_counts"] = json.dumps([d["count"] for d in type_data])

        return ctx
