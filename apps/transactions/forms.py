"""Formulaires : demandes de visite/info + édition transactions."""
from django import forms
from .models import InfoRequest, Transaction, TransactionStep, VisitRequest


class VisitRequestForm(forms.ModelForm):
    """Formulaire de demande de visite (depuis la fiche du bien)."""

    class Meta:
        model = VisitRequest
        fields = ("full_name", "email", "phone", "preferred_date", "preferred_time", "message")
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "preferred_time": forms.TimeInput(attrs={"type": "time"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }


class InfoRequestForm(forms.ModelForm):
    """Formulaire de demande d'informations."""

    class Meta:
        model = InfoRequest
        fields = ("full_name", "email", "phone", "question")
        widgets = {"question": forms.Textarea(attrs={"rows": 4})}


class VisitRequestUpdateForm(forms.ModelForm):
    """Pour les agents — mise à jour du statut + notes."""

    class Meta:
        model = VisitRequest
        fields = ("status", "confirmed_date", "agent_notes")
        widgets = {
            "confirmed_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "agent_notes": forms.Textarea(attrs={"rows": 3}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        exclude = ("created_at", "updated_at", "signed_at")
        widgets = {
            "offer_date": forms.DateInput(attrs={"type": "date"}),
            "expected_signature_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class TransactionStepForm(forms.ModelForm):
    class Meta:
        model = TransactionStep
        fields = ("title", "description", "is_completed", "visible_to_client")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}
