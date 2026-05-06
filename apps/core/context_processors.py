"""Variables disponibles dans tous les templates."""
from django.conf import settings


def site_settings(request):
    return {
        "SITE_NAME": "Ymmo",
        "SITE_BASELINE": "Votre partenaire immobilier de confiance",
        "DEBUG": settings.DEBUG,
    }
