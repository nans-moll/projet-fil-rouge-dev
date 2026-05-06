"""Tests basiques pour valider modèles, services et accès aux vues."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.properties.models import Agency, Property
from apps.properties.services import PropertySearchService

User = get_user_model()


@pytest.fixture
def agency(db):
    return Agency.objects.create(
        name="Ymmo Test", city="Aix-en-Provence", postal_code="13100",
        address="1 cours Mirabeau", phone="0400000000", email="test@ymmo.fr",
    )


@pytest.fixture
def agent(db, agency):
    user = User.objects.create_user(
        username="agent_test", password="Agent12345!", email="agent@ymmo.fr",
        role=User.Role.AGENT, agency=agency,
    )
    return user


@pytest.fixture
def property_obj(db, agency, agent):
    return Property.objects.create(
        reference="TEST001", title="Appartement test",
        description="Test", property_type=Property.Type.APARTMENT,
        transaction_type=Property.Transaction.SALE,
        status=Property.Status.AVAILABLE,
        surface=80, rooms=3, bedrooms=2, bathrooms=1,
        price=Decimal("250000"), agency=agency, agent=agent,
        address="10 rue test", city="Aix-en-Provence", postal_code="13100",
    )


class TestPropertyModel:
    def test_str(self, property_obj):
        assert "TEST001" in str(property_obj)

    def test_price_per_sqm(self, property_obj):
        assert property_obj.price_per_sqm == Decimal("3125.00")

    def test_total_price_with_fees(self, property_obj):
        # 250 000 * 1.04 = 260 000
        assert property_obj.total_price_with_fees == Decimal("260000.00")

    def test_slug_generated(self, property_obj):
        assert property_obj.slug.startswith("test001")


class TestUserRoles:
    def test_role_helpers(self, agent):
        assert agent.is_agent
        assert not agent.is_client
        assert not agent.is_admin


class TestSearchService:
    def test_search_by_city(self, db, property_obj):
        results = PropertySearchService.search({"city": "Aix"})
        assert property_obj in results

    def test_search_by_max_price(self, db, property_obj):
        # Plus cher que le bien → exclut
        cheap = PropertySearchService.search({"max_price": 100_000})
        assert property_obj not in cheap

        # Au-dessus du prix → inclut
        ok = PropertySearchService.search({"max_price": 300_000})
        assert property_obj in ok

    def test_only_available(self, db, property_obj):
        property_obj.status = Property.Status.DRAFT
        property_obj.save()
        results = PropertySearchService.search({})
        assert property_obj not in results


class TestPublicViews:
    def test_home(self, client, db):
        response = client.get(reverse("core:home"))
        assert response.status_code == 200

    def test_property_list(self, client, db):
        response = client.get(reverse("properties:list"))
        assert response.status_code == 200

    def test_login_page(self, client, db):
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200


class TestAccessControl:
    def test_client_dashboard_requires_login(self, client, db):
        response = client.get(reverse("transactions:client_dashboard"))
        assert response.status_code in (302, 403)

    def test_agent_dashboard_requires_agent_role(self, client, db):
        # Visiteur non connecté
        response = client.get(reverse("transactions:agent_dashboard"))
        assert response.status_code in (302, 403)
