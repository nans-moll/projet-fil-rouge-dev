"""Vues : demandes de visite/info, dashboards, transactions."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DetailView, ListView, TemplateView, UpdateView,
)

from apps.accounts.decorators import AgentRequiredMixin, ClientRequiredMixin
from apps.properties.models import Property

from .forms import (
    InfoRequestForm, TransactionForm, TransactionStepForm,
    VisitRequestForm, VisitRequestUpdateForm,
)
from .models import InfoRequest, Transaction, TransactionStep, VisitRequest


# ---------- Demandes (publique : depuis la fiche du bien) ----------

def request_visit(request, property_pk):
    """Demande de visite depuis la fiche du bien."""
    prop = get_object_or_404(Property, pk=property_pk)
    if request.method == "POST":
        form = VisitRequestForm(request.POST)
        if form.is_valid():
            vr = form.save(commit=False)
            vr.property = prop
            if request.user.is_authenticated:
                vr.client = request.user
                vr.full_name = vr.full_name or request.user.get_full_name()
                vr.email = vr.email or request.user.email
            vr.save()
            messages.success(
                request,
                "Votre demande de visite a été transmise à l'agence. Vous serez recontacté(e) sous 24h.",
            )
            return redirect("properties:detail", slug=prop.slug)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                "full_name": request.user.get_full_name(),
                "email": request.user.email,
                "phone": request.user.phone,
            }
        form = VisitRequestForm(initial=initial)
    return render(request, "transactions/request_visit.html",
                  {"form": form, "property": prop})


def request_info(request, property_pk):
    prop = get_object_or_404(Property, pk=property_pk)
    if request.method == "POST":
        form = InfoRequestForm(request.POST)
        if form.is_valid():
            ir = form.save(commit=False)
            ir.property = prop
            if request.user.is_authenticated:
                ir.client = request.user
            ir.save()
            messages.success(request, "Demande envoyée à l'agence.")
            return redirect("properties:detail", slug=prop.slug)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                "full_name": request.user.get_full_name(),
                "email": request.user.email,
                "phone": request.user.phone,
            }
        form = InfoRequestForm(initial=initial)
    return render(request, "transactions/request_info.html",
                  {"form": form, "property": prop})


# ---------- Dashboard CLIENT ----------

class ClientDashboardView(ClientRequiredMixin, TemplateView):
    """Tableau de bord client : favoris, demandes, transactions."""

    template_name = "transactions/client/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["visit_requests"] = (
            VisitRequest.objects.filter(client=u).select_related("property")[:10]
        )
        ctx["info_requests"] = (
            InfoRequest.objects.filter(client=u).select_related("property")[:10]
        )
        ctx["transactions"] = (
            Transaction.objects.filter(buyer=u).select_related("property", "agent")
        )
        ctx["favorites"] = u.favorites.select_related("property").prefetch_related("property__photos")[:8]
        return ctx


class ClientTransactionDetailView(ClientRequiredMixin, DetailView):
    model = Transaction
    template_name = "transactions/client/transaction_detail.html"
    context_object_name = "transaction"

    def get_queryset(self):
        return Transaction.objects.filter(buyer=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["steps"] = self.object.steps.filter(visible_to_client=True)
        return ctx


# ---------- Dashboard AGENT ----------

class AgentDashboardView(AgentRequiredMixin, TemplateView):
    template_name = "transactions/agent/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        properties = (
            Property.objects.all() if u.is_admin
            else Property.objects.filter(agency=u.agency)
        )

        # KPIs principaux
        ctx["total_properties"] = properties.count()
        ctx["available_properties"] = properties.filter(status=Property.Status.AVAILABLE).count()
        ctx["sold_properties"] = properties.filter(status=Property.Status.SOLD).count()
        ctx["total_views"] = properties.aggregate(Sum("views_count"))["views_count__sum"] or 0

        ctx["pending_visits"] = (
            VisitRequest.objects.filter(
                property__in=properties, status=VisitRequest.Status.PENDING,
            ).select_related("property", "client")[:10]
        )
        ctx["pending_infos"] = (
            InfoRequest.objects.filter(
                property__in=properties, answered_at__isnull=True,
            ).select_related("property", "client")[:10]
        )
        ctx["active_transactions"] = (
            Transaction.objects.filter(property__in=properties)
            .exclude(status__in=[Transaction.Status.SIGNED, Transaction.Status.CANCELLED])
            .select_related("property", "buyer")
        )

        # Stats par type
        ctx["by_type"] = (
            properties.values("property_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        ctx["avg_price"] = properties.aggregate(Avg("price"))["price__avg"] or 0

        return ctx


class AgentVisitListView(AgentRequiredMixin, ListView):
    model = VisitRequest
    template_name = "transactions/agent/visit_list.html"
    context_object_name = "visits"
    paginate_by = 30

    def get_queryset(self):
        u = self.request.user
        qs = VisitRequest.objects.select_related("property", "client")
        if not u.is_admin:
            qs = qs.filter(property__agency=u.agency)
        return qs


class AgentVisitUpdateView(AgentRequiredMixin, UpdateView):
    model = VisitRequest
    form_class = VisitRequestUpdateForm
    template_name = "transactions/agent/visit_update.html"
    success_url = reverse_lazy("transactions:agent_visit_list")

    def get_queryset(self):
        u = self.request.user
        if u.is_admin:
            return VisitRequest.objects.all()
        return VisitRequest.objects.filter(property__agency=u.agency)

    def form_valid(self, form):
        messages.success(self.request, "Demande de visite mise à jour.")
        return super().form_valid(form)


class AgentTransactionListView(AgentRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/agent/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 25

    def get_queryset(self):
        u = self.request.user
        qs = Transaction.objects.select_related("property", "buyer", "agent")
        if u.is_admin:
            return qs
        return qs.filter(property__agency=u.agency)


class AgentTransactionCreateView(AgentRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/agent/transaction_form.html"

    def form_valid(self, form):
        form.instance.agent = self.request.user
        messages.success(self.request, "Transaction créée.")
        return super().form_valid(form)


class AgentTransactionUpdateView(AgentRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/agent/transaction_form.html"

    def get_queryset(self):
        u = self.request.user
        if u.is_admin:
            return Transaction.objects.all()
        return Transaction.objects.filter(property__agency=u.agency)

    def form_valid(self, form):
        # Marque comme signé si statut SIGNED
        if form.instance.status == Transaction.Status.SIGNED and not form.instance.signed_at:
            form.instance.signed_at = timezone.now()
        return super().form_valid(form)


class AgentTransactionDetailView(AgentRequiredMixin, DetailView):
    model = Transaction
    template_name = "transactions/agent/transaction_detail.html"
    context_object_name = "transaction"

    def get_queryset(self):
        u = self.request.user
        if u.is_admin:
            return Transaction.objects.all()
        return Transaction.objects.filter(property__agency=u.agency)


@login_required
def add_transaction_step(request, pk):
    if not (request.user.is_agent or request.user.is_admin):
        raise PermissionDenied
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.user.is_agent and transaction.property.agency != request.user.agency:
        raise PermissionDenied
    if request.method == "POST":
        form = TransactionStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.transaction = transaction
            if step.is_completed:
                step.completed_at = timezone.now()
            step.save()
            messages.success(request, "Étape ajoutée.")
            return redirect("transactions:agent_transaction_detail", pk=pk)
    else:
        form = TransactionStepForm()
    return render(request, "transactions/agent/step_form.html",
                  {"form": form, "transaction": transaction})
