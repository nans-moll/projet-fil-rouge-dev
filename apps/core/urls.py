from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("a-propos/", views.AboutView.as_view(), name="about"),
    path("agences/", views.AgenciesView.as_view(), name="agencies"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("mentions-legales/", views.LegalView.as_view(), name="legal"),
]
