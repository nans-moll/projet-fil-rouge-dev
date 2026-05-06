from django.urls import path
from . import views

app_name = "properties"

urlpatterns = [
    # Public
    path("", views.PropertyListView.as_view(), name="list"),
    path("favori/<int:pk>/", views.toggle_favorite, name="toggle_favorite"),
    path("agence/<slug:slug>/", views.AgencyDetailView.as_view(), name="agency_detail"),

    # CRUD agents
    path("gestion/", views.AgentPropertyListView.as_view(), name="agent_list"),
    path("gestion/nouveau/", views.PropertyCreateView.as_view(), name="agent_create"),
    path("gestion/<int:pk>/modifier/", views.PropertyUpdateView.as_view(), name="agent_update"),
    path("gestion/<int:pk>/supprimer/", views.PropertyDeleteView.as_view(), name="agent_delete"),
    path("gestion/<int:pk>/photo/", views.add_photo, name="agent_add_photo"),
    path("gestion/photo/<int:pk>/supprimer/", views.delete_photo, name="agent_delete_photo"),

    # Détail (slug en dernier pour ne pas capturer les autres routes)
    path("<slug:slug>/", views.PropertyDetailView.as_view(), name="detail"),
]
