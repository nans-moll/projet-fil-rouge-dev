"""
Modèles de transactions immobilières.

- VisitRequest : demande de visite faite par un client
- InfoRequest : demande d'informations sur un bien
- Transaction : transaction (vente/location) en cours ou aboutie
- TransactionStep : étape de suivi d'une transaction (timeline client)
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.properties.models import Property, TimestampedModel


class VisitRequest(TimestampedModel):
    """Demande de visite d'un bien par un client."""

    class Status(models.TextChoices):
        PENDING = "PENDING", _("En attente")
        CONFIRMED = "CONFIRMED", _("Confirmée")
        DONE = "DONE", _("Effectuée")
        CANCELLED = "CANCELLED", _("Annulée")

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="visit_requests",
        verbose_name=_("Bien"),
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="visit_requests",
        verbose_name=_("Client"),
    )
    # Permet aussi les demandes anonymes (visiteurs non connectés)
    full_name = models.CharField(_("Nom"), max_length=120)
    email = models.EmailField()
    phone = models.CharField(_("Téléphone"), max_length=20, blank=True)

    preferred_date = models.DateField(_("Date souhaitée"), null=True, blank=True)
    preferred_time = models.TimeField(_("Heure souhaitée"), null=True, blank=True)
    message = models.TextField(_("Message"), blank=True)

    status = models.CharField(
        _("Statut"), max_length=15,
        choices=Status.choices, default=Status.PENDING,
    )
    confirmed_date = models.DateTimeField(_("Date confirmée"), null=True, blank=True)
    agent_notes = models.TextField(_("Notes agent"), blank=True)

    class Meta:
        verbose_name = _("Demande de visite")
        verbose_name_plural = _("Demandes de visite")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Visite {self.property.reference} — {self.full_name}"


class InfoRequest(TimestampedModel):
    """Demande d'informations supplémentaires sur un bien."""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="info_requests",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="info_requests",
    )
    full_name = models.CharField(_("Nom"), max_length=120)
    email = models.EmailField()
    phone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    question = models.TextField(_("Question"))
    answered_at = models.DateTimeField(null=True, blank=True)
    response = models.TextField(_("Réponse"), blank=True)

    class Meta:
        verbose_name = _("Demande d'informations")
        verbose_name_plural = _("Demandes d'informations")
        ordering = ["-created_at"]


class Transaction(TimestampedModel):
    """
    Transaction immobilière (vente ou location).

    Reflète l'avancement d'un dossier d'achat/vente. Les agents la créent
    et la pilotent ; les clients la suivent en lecture.
    """

    class Type(models.TextChoices):
        SALE = "SALE", _("Vente")
        RENT = "RENT", _("Location")

    class Status(models.TextChoices):
        OFFER_MADE = "OFFER_MADE", _("Offre déposée")
        OFFER_ACCEPTED = "OFFER_ACCEPTED", _("Offre acceptée")
        COMPROMISE = "COMPROMISE", _("Compromis signé")
        FINANCING = "FINANCING", _("Financement en cours")
        SIGNED = "SIGNED", _("Acte signé")
        CANCELLED = "CANCELLED", _("Annulée")

    reference = models.CharField(_("Référence"), max_length=20, unique=True)
    property = models.ForeignKey(
        Property, on_delete=models.PROTECT, related_name="transactions",
    )
    type = models.CharField(_("Type"), max_length=10, choices=Type.choices, default=Type.SALE)
    status = models.CharField(
        _("Statut"), max_length=20,
        choices=Status.choices, default=Status.OFFER_MADE,
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="purchases", verbose_name=_("Acheteur/Locataire"),
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="sales", verbose_name=_("Vendeur"),
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="managed_transactions", verbose_name=_("Agent référent"),
    )

    offer_price = models.DecimalField(_("Prix proposé (€)"), max_digits=12, decimal_places=2)
    final_price = models.DecimalField(
        _("Prix final (€)"), max_digits=12, decimal_places=2,
        null=True, blank=True,
    )
    agency_commission = models.DecimalField(
        _("Commission agence (€)"), max_digits=10, decimal_places=2,
        default=Decimal("0"),
    )

    offer_date = models.DateField(_("Date offre"))
    expected_signature_date = models.DateField(_("Signature prévue"), null=True, blank=True)
    signed_at = models.DateTimeField(_("Signé le"), null=True, blank=True)

    notes = models.TextField(_("Notes internes"), blank=True)

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.property.title}"

    def get_absolute_url(self):
        return reverse("transactions:detail", kwargs={"pk": self.pk})

    def progress_percent(self) -> int:
        """Pourcentage d'avancement basé sur le statut. (Méthode, pas property,
        car le champ FK `property` shadow le décorateur built-in.)"""
        progression = {
            self.Status.OFFER_MADE: 20,
            self.Status.OFFER_ACCEPTED: 40,
            self.Status.COMPROMISE: 60,
            self.Status.FINANCING: 80,
            self.Status.SIGNED: 100,
            self.Status.CANCELLED: 0,
        }
        return progression.get(self.status, 0)


class TransactionStep(TimestampedModel):
    """Étape d'une transaction (visible côté client : timeline du dossier)."""

    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="steps",
    )
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    visible_to_client = models.BooleanField(_("Visible client"), default=True)

    class Meta:
        verbose_name = _("Étape de transaction")
        verbose_name_plural = _("Étapes de transactions")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.transaction.reference} — {self.title}"
