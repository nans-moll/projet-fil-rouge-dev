"""Formulaires de recherche et CRUD biens."""
from django import forms

from .models import Agency, Property, PropertyImage


class PropertySearchForm(forms.Form):
    """Recherche publique multi-critères."""

    query = forms.CharField(
        required=False, label="Recherche",
        widget=forms.TextInput(attrs={"placeholder": "Ville, référence, mot-clé…"}),
    )
    transaction_type = forms.ChoiceField(
        required=False, label="Transaction",
        choices=[("", "Tous")] + list(Property.Transaction.choices),
    )
    property_type = forms.ChoiceField(
        required=False, label="Type",
        choices=[("", "Tous")] + list(Property.Type.choices),
    )
    city = forms.CharField(required=False, label="Ville")
    min_price = forms.IntegerField(required=False, label="Prix min", min_value=0)
    max_price = forms.IntegerField(required=False, label="Prix max", min_value=0)
    min_surface = forms.IntegerField(required=False, label="Surface min", min_value=0)
    min_rooms = forms.IntegerField(required=False, label="Pièces min", min_value=1)
    has_garage = forms.BooleanField(required=False, label="Garage")
    has_garden = forms.BooleanField(required=False, label="Jardin")
    has_pool = forms.BooleanField(required=False, label="Piscine")

    SORT_CHOICES = [
        ("-published_at", "Plus récent"),
        ("price", "Prix croissant"),
        ("-price", "Prix décroissant"),
        ("-surface", "Plus grande surface"),
    ]
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES, label="Trier")


class PropertyForm(forms.ModelForm):
    """CRUD bien — utilisé par les agents."""

    class Meta:
        model = Property
        exclude = ("created_at", "updated_at", "slug", "views_count", "published_at")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user and user.is_agent and user.agency:
            # Un agent ne peut publier que pour son agence
            self.fields["agency"].queryset = Agency.objects.filter(pk=user.agency.pk)
            self.fields["agency"].initial = user.agency
            self.fields["agency"].disabled = True


class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ("image", "caption", "is_main", "order")
