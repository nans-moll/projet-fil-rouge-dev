from django.urls import path
from . import views

app_name = "transactions"

urlpatterns = [
    # Demandes (publiques)
    path("bien/<int:property_pk>/visite/", views.request_visit, name="request_visit"),
    path("bien/<int:property_pk>/info/", views.request_info, name="request_info"),

    # Dashboard CLIENT
    path("mon-espace/", views.ClientDashboardView.as_view(), name="client_dashboard"),
    path("mon-espace/dossier/<int:pk>/",
         views.ClientTransactionDetailView.as_view(), name="client_transaction_detail"),

    # Dashboard AGENT
    path("agent/", views.AgentDashboardView.as_view(), name="agent_dashboard"),
    path("agent/visites/", views.AgentVisitListView.as_view(), name="agent_visit_list"),
    path("agent/visites/<int:pk>/",
         views.AgentVisitUpdateView.as_view(), name="agent_visit_update"),

    path("agent/transactions/",
         views.AgentTransactionListView.as_view(), name="agent_transaction_list"),
    path("agent/transactions/nouveau/",
         views.AgentTransactionCreateView.as_view(), name="agent_transaction_create"),
    path("agent/transactions/<int:pk>/",
         views.AgentTransactionDetailView.as_view(), name="agent_transaction_detail"),
    path("agent/transactions/<int:pk>/modifier/",
         views.AgentTransactionUpdateView.as_view(), name="agent_transaction_update"),
    path("agent/transactions/<int:pk>/etape/",
         views.add_transaction_step, name="agent_add_step"),
]
