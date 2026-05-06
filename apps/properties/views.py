"""Vues publiques + CRUD agents pour les biens."""
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from apps.accounts.decorators import AgentRequiredMixin

from .forms import PropertyForm, PropertyImageForm, PropertySearchForm
from .models import Agency, FavoriteProperty, Property, PropertyImage
from .services import PropertySearchService


# ---------- Vues publiques ----------

class PropertyListView(ListView):
    """Liste publique des biens avec recherche et pagination."""

    model = Property
    template_name = "properties/list.html"
    context_object_name = "properties"
    paginate_by = 12

    def get_queryset(self):
        form = PropertySearchForm(self.request.GET or None)
        filters = form.cleaned_data if form.is_valid() else {}
        return PropertySearchService.search(filters)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_form"] = PropertySearchForm(self.request.GET or None)
        ctx["total_results"] = self.get_queryset().count()
        return ctx


class PropertyDetailView(DetailView):
    """Fiche détaillée d'un bien."""

    model = Property
    template_name = "properties/detail.html"
    context_object_name = "property"

    def get_queryset(self):
        return (
            Property.objects.filter(status=Property.Status.AVAILABLE)
            .select_related("agency", "agent")
            .prefetch_related("photos")
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.increment_views()
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        prop = self.object
        # Biens similaires (même type, même ville, prix ±20%)
        ctx["similar_properties"] = (
            Property.objects.filter(
                status=Property.Status.AVAILABLE,
                property_type=prop.property_type,
                city=prop.city,
                price__gte=prop.price * Decimal("0.8"),
                price__lte=prop.price * Decimal("1.2"),
            )
            .exclude(pk=prop.pk)
            .select_related("agency")
            .prefetch_related("photos")[:4]
        )
        if self.request.user.is_authenticated:
            ctx["is_favorite"] = FavoriteProperty.objects.filter(
                user=self.request.user, property=prop
            ).exists()
        return ctx


class AgencyDetailView(DetailView):
    model = Agency
    template_name = "properties/agency_detail.html"
    context_object_name = "agency"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["properties"] = (
            self.object.properties.filter(status=Property.Status.AVAILABLE)
            .prefetch_related("photos")[:12]
        )
        return ctx


@login_required
def toggle_favorite(request, pk):
    """Ajoute/retire un bien des favoris."""
    prop = get_object_or_404(Property, pk=pk)
    fav, created = FavoriteProperty.objects.get_or_create(
        user=request.user, property=prop
    )
    if not created:
        fav.delete()
        messages.info(request, "Bien retiré des favoris.")
    else:
        messages.success(request, "Bien ajouté aux favoris.")
    return redirect("properties:detail", slug=prop.slug)


# ---------- CRUD agents ----------

class AgentPropertyListView(AgentRequiredMixin, ListView):
    """Liste des biens gérés par l'agent connecté."""

    model = Property
    template_name = "properties/agent/list.html"
    context_object_name = "properties"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        qs = Property.objects.select_related("agency", "agent").prefetch_related("photos")
        if user.is_admin:
            return qs
        return qs.filter(agency=user.agency)


class PropertyCreateView(AgentRequiredMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = "properties/agent/form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.agent = self.request.user
        if form.instance.status == Property.Status.AVAILABLE and not form.instance.published_at:
            form.instance.published_at = timezone.now()
        messages.success(self.request, "Bien créé.")
        return super().form_valid(form)


class PropertyUpdateView(AgentRequiredMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = "properties/agent/form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Property.objects.all()
        return Property.objects.filter(agency=user.agency)

    def form_valid(self, form):
        if form.instance.status == Property.Status.AVAILABLE and not form.instance.published_at:
            form.instance.published_at = timezone.now()
        messages.success(self.request, "Bien mis à jour.")
        return super().form_valid(form)


class PropertyDeleteView(AgentRequiredMixin, DeleteView):
    model = Property
    template_name = "properties/agent/delete.html"
    success_url = reverse_lazy("properties:agent_list")

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Property.objects.all()
        return Property.objects.filter(agency=user.agency)


@login_required
def add_photo(request, pk):
    """Ajoute une photo à un bien (agents seulement)."""
    if not (request.user.is_agent or request.user.is_admin):
        raise PermissionDenied
    prop = get_object_or_404(Property, pk=pk)
    if request.user.is_agent and prop.agency != request.user.agency:
        raise PermissionDenied
    if request.method == "POST":
        form = PropertyImageForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.property = prop
            photo.save()
            messages.success(request, "Photo ajoutée.")
            return redirect("properties:agent_update", pk=prop.pk)
    else:
        form = PropertyImageForm()
    return render(request, "properties/agent/photo_form.html", {"form": form, "property": prop})


@login_required
def delete_photo(request, pk):
    photo = get_object_or_404(PropertyImage, pk=pk)
    if not (request.user.is_admin or
            (request.user.is_agent and photo.property.agency == request.user.agency)):
        raise PermissionDenied
    prop_pk = photo.property.pk
    photo.delete()
    messages.info(request, "Photo supprimée.")
    return redirect("properties:agent_update", pk=prop_pk)
