"""
Modèles du domaine immobilier.

Conception POO :
- `TimestampedModel` : classe abstraite mutualisant created_at / updated_at (DRY).
- `Agency` : agence Ymmo (siège + 12 antennes).
- `Property` : bien immobilier (résidentiel ou professionnel).
- `PropertyImage` : photos d'un bien.
- `PropertyType` : enum des types (maison, appartement, local, terrain…).
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    """Classe abstraite — ajoute created_at / updated_at."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Agency(TimestampedModel):
    """Agence du réseau Ymmo (siège + 12 agences locales)."""

    name = models.CharField(_("Nom"), max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    is_headquarters = models.BooleanField(_("Siège social"), default=False)

    # Adresse
    address = models.CharField(_("Adresse"), max_length=255)
    city = models.CharField(_("Ville"), max_length=100)
    postal_code = models.CharField(_("Code postal"), max_length=10)
    region = models.CharField(_("Région"), max_length=100, blank=True)

    # Contact
    phone = models.CharField(_("Téléphone"), max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)

    # Géoloc (pour la carte)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Agence")
        verbose_name_plural = _("Agences")
        ordering = ["-is_headquarters", "city"]

    def __str__(self):
        prefix = "[Siège] " if self.is_headquarters else ""
        return f"{prefix}{self.name} ({self.city})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city}")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("properties:agency_detail", kwargs={"slug": self.slug})

    @property
    def active_properties_count(self) -> int:
        return self.properties.filter(status=Property.Status.AVAILABLE).count()


class Property(TimestampedModel):
    """Bien immobilier proposé par une agence."""

    class Type(models.TextChoices):
        APARTMENT = "APARTMENT", _("Appartement")
        HOUSE = "HOUSE", _("Maison")
        LAND = "LAND", _("Terrain")
        COMMERCIAL = "COMMERCIAL", _("Local commercial")
        OFFICE = "OFFICE", _("Bureau")
        BUILDING = "BUILDING", _("Immeuble")
        OTHER = "OTHER", _("Autre")

    class Transaction(models.TextChoices):
        SALE = "SALE", _("Vente")
        RENT = "RENT", _("Location")

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Brouillon")
        AVAILABLE = "AVAILABLE", _("Disponible")
        UNDER_OFFER = "UNDER_OFFER", _("Sous compromis")
        SOLD = "SOLD", _("Vendu")
        WITHDRAWN = "WITHDRAWN", _("Retiré")

    class EnergyClass(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"
        E = "E", "E"
        F = "F", "F"
        G = "G", "G"

    # Identification
    reference = models.CharField(_("Référence"), max_length=20, unique=True)
    title = models.CharField(_("Titre"), max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(_("Description"))

    # Classification
    property_type = models.CharField(_("Type"), max_length=15, choices=Type.choices)
    transaction_type = models.CharField(
        _("Transaction"), max_length=10, choices=Transaction.choices,
        default=Transaction.SALE,
    )
    status = models.CharField(
        _("Statut"), max_length=15, choices=Status.choices,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField(_("À la une"), default=False)

    # Caractéristiques
    surface = models.PositiveIntegerField(_("Surface (m²)"))
    land_surface = models.PositiveIntegerField(_("Surface terrain (m²)"), null=True, blank=True)
    rooms = models.PositiveIntegerField(_("Nombre de pièces"), default=1)
    bedrooms = models.PositiveIntegerField(_("Chambres"), default=0)
    bathrooms = models.PositiveIntegerField(_("Salles de bain"), default=0)
    floor = models.IntegerField(_("Étage"), null=True, blank=True)
    has_garage = models.BooleanField(_("Garage"), default=False)
    has_garden = models.BooleanField(_("Jardin"), default=False)
    has_pool = models.BooleanField(_("Piscine"), default=False)
    has_balcony = models.BooleanField(_("Balcon/Terrasse"), default=False)
    has_elevator = models.BooleanField(_("Ascenseur"), default=False)
    is_furnished = models.BooleanField(_("Meublé"), default=False)
    energy_class = models.CharField(
        _("Classe énergétique"), max_length=1, choices=EnergyClass.choices,
        blank=True,
    )
    construction_year = models.PositiveIntegerField(
        _("Année de construction"), null=True, blank=True
    )

    # Prix
    price = models.DecimalField(_("Prix (€)"), max_digits=12, decimal_places=2)
    monthly_charges = models.DecimalField(
        _("Charges mensuelles (€)"), max_digits=8, decimal_places=2,
        null=True, blank=True,
    )
    agency_fees_percent = models.DecimalField(
        _("Frais d'agence (%)"), max_digits=4, decimal_places=2,
        default=Decimal("4.00"),
    )

    # Localisation
    address = models.CharField(_("Adresse"), max_length=255)
    city = models.CharField(_("Ville"), max_length=100)
    postal_code = models.CharField(_("Code postal"), max_length=10)
    region = models.CharField(_("Région"), max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Liens
    agency = models.ForeignKey(
        Agency, on_delete=models.PROTECT, related_name="properties",
        verbose_name=_("Agence"),
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="managed_properties",
        verbose_name=_("Agent référent"),
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="properties_for_sale",
        verbose_name=_("Vendeur"),
    )

    # Stats
    views_count = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Bien")
        verbose_name_plural = _("Biens")
        ordering = ["-is_featured", "-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "transaction_type"]),
            models.Index(fields=["city"]),
            models.Index(fields=["price"]),
            models.Index(fields=["property_type"]),
        ]

    def __str__(self):
        return f"{self.reference} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.reference}-{self.title}")[:220]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("properties:detail", kwargs={"slug": self.slug})

    @property
    def main_photo(self):
        return self.photos.filter(is_main=True).first() or self.photos.first()

    @property
    def price_per_sqm(self) -> Decimal:
        if self.surface > 0:
            return (self.price / self.surface).quantize(Decimal("0.01"))
        return Decimal("0")

    @property
    def total_price_with_fees(self) -> Decimal:
        fees = self.price * self.agency_fees_percent / Decimal("100")
        return (self.price + fees).quantize(Decimal("0.01"))

    def increment_views(self):
        Property.objects.filter(pk=self.pk).update(views_count=models.F("views_count") + 1)


class PropertyImage(TimestampedModel):
    """Photo d'un bien (un bien peut en avoir plusieurs)."""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="photos",
        verbose_name=_("Bien"),
    )
    image = models.ImageField(_("Image"), upload_to="properties/%Y/%m/")
    caption = models.CharField(_("Légende"), max_length=200, blank=True)
    is_main = models.BooleanField(_("Photo principale"), default=False)
    order = models.PositiveSmallIntegerField(_("Ordre"), default=0)

    class Meta:
        verbose_name = _("Photo de bien")
        verbose_name_plural = _("Photos de biens")
        ordering = ["-is_main", "order", "created_at"]

    def __str__(self):
        return f"Photo de {self.property.reference}"

    def save(self, *args, **kwargs):
        # Une seule photo principale par bien
        if self.is_main:
            PropertyImage.objects.filter(
                property=self.property, is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)


class FavoriteProperty(TimestampedModel):
    """Bien mis en favori par un utilisateur (client)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="favorites",
    )
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="favorited_by",
    )

    class Meta:
        verbose_name = _("Favori")
        verbose_name_plural = _("Favoris")
        unique_together = [("user", "property")]
        ordering = ["-created_at"]
