"""Vues publiques (pages statiques + home avec biens en avant)."""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView, ListView

from apps.properties.models import Property, Agency
from .forms import ContactForm
from .models import ContactMessage


class HomeView(ListView):
    """Page d'accueil avec les biens en avant et la barre de recherche."""

    model = Property
    template_name = "core/home.html"
    context_object_name = "featured_properties"

    def get_queryset(self):
        return (
            Property.objects.filter(status=Property.Status.AVAILABLE, is_featured=True)
            .select_related("agency")
            .prefetch_related("photos")[:6]
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["agencies_count"] = Agency.objects.count()
        ctx["properties_count"] = Property.objects.filter(status=Property.Status.AVAILABLE).count()
        ctx["cities_count"] = (
            Property.objects.values("city").distinct().count()
        )
        return ctx


class AboutView(TemplateView):
    template_name = "core/about.html"


class AgenciesView(ListView):
    model = Agency
    template_name = "core/agencies.html"
    context_object_name = "agencies"
    paginate_by = 24


class LegalView(TemplateView):
    template_name = "core/legal.html"


class ContactView(FormView):
    template_name = "core/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("core:contact")

    def form_valid(self, form):
        ContactMessage.objects.create(**form.cleaned_data)
        messages.success(
            self.request,
            "Votre message a bien été envoyé. Une de nos agences vous répondra sous 48h.",
        )
        return super().form_valid(form)
