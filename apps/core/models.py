"""Modèles transverses (messages de contact)."""
from django.db import models


class ContactMessage(models.Model):
    """Message envoyé via le formulaire de contact public."""

    full_name = models.CharField("Nom complet", max_length=120)
    email = models.EmailField()
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    subject = models.CharField("Sujet", max_length=200)
    message = models.TextField()
    is_processed = models.BooleanField("Traité", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.subject}"
