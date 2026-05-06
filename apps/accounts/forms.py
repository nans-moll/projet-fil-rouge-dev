"""Formulaires d'authentification et de profil."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class LoginForm(AuthenticationForm):
    """Connexion par email ou username."""

    username = forms.CharField(label="Email ou identifiant", max_length=150)


class ClientRegisterForm(UserCreationForm):
    """Inscription publique : crée toujours un compte client."""

    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")
    phone = forms.CharField(max_length=20, required=False, label="Téléphone")

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone",
                  "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte avec cet email existe déjà.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLIENT
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone = self.cleaned_data.get("phone", "")
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Édition du profil par l'utilisateur connecté."""

    class Meta:
        model = User
        fields = (
            "first_name", "last_name", "email", "phone", "avatar",
            "address", "city", "postal_code",
            "search_min_price", "search_max_price", "search_city",
        )
