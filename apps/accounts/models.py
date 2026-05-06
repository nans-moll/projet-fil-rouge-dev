"""Modèle User personnalisé avec gestion des rôles métier."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Utilisateur étendu avec un système de rôles.

    Trois rôles métier :
    - ADMIN : direction Ymmo, accès complet
    - AGENT : commerciaux d'agence (CRUD biens, dossiers clients de leur agence)
    - CLIENT : acheteurs/vendeurs (consultation, demandes de visite, suivi)
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", _("Administrateur")
        AGENT = "AGENT", _("Agent immobilier")
        CLIENT = "CLIENT", _("Client")

    role = models.CharField(
        _("Rôle"),
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    phone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    avatar = models.ImageField(_("Photo de profil"), upload_to="avatars/", blank=True, null=True)

    # Champs spécifiques agents
    agency = models.ForeignKey(
        "properties.Agency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents",
        verbose_name=_("Agence de rattachement"),
    )

    # Champs spécifiques clients
    address = models.CharField(_("Adresse"), max_length=255, blank=True)
    city = models.CharField(_("Ville"), max_length=100, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=10, blank=True)

    # Préférences de recherche (utilisées pour notifications futures)
    search_min_price = models.PositiveIntegerField(
        _("Prix min recherché"), null=True, blank=True
    )
    search_max_price = models.PositiveIntegerField(
        _("Prix max recherché"), null=True, blank=True
    )
    search_city = models.CharField(_("Ville recherchée"), max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        ordering = ["-created_at"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_agent(self) -> bool:
        return self.role == self.Role.AGENT

    @property
    def is_client(self) -> bool:
        return self.role == self.Role.CLIENT

    def get_absolute_url(self):
        return reverse("accounts:profile")

    def get_dashboard_url(self):
        """Retourne l'URL du tableau de bord adapté au rôle."""
        if self.is_admin:
            return reverse("admin:index")
        if self.is_agent:
            return reverse("transactions:agent_dashboard")
        return reverse("transactions:client_dashboard")
