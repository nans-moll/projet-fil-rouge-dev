"""
Génère un jeu de données de démonstration pour Ymmo.

Usage : python manage.py seed_demo [--reset]

Crée :
- 1 super-admin (admin / admin@ymmo.fr / Admin12345!)
- 13 agences (1 siège + 12 antennes)
- 13 agents (1 par agence)
- 30 clients
- ~200 biens immobiliers répartis dans toute la France
- Quelques demandes de visite et transactions pour la démo
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.properties.models import Agency, Property, FavoriteProperty
from apps.transactions.models import (
    InfoRequest, Transaction as Tx, TransactionStep, VisitRequest,
)

User = get_user_model()

# Données de référence (12 agences en France + siège Aix)
AGENCIES_DATA = [
    # (name, city, postal, address, region, phone, is_hq)
    ("Ymmo Aix Siège", "Aix-en-Provence", "13100", "12 cours Mirabeau", "PACA", "04 42 00 00 00", True),
    ("Ymmo Marseille", "Marseille", "13001", "1 rue de la République", "PACA", "04 91 00 00 00", False),
    ("Ymmo Lyon", "Lyon", "69002", "8 place Bellecour", "Auvergne-Rhône-Alpes", "04 78 00 00 00", False),
    ("Ymmo Paris Nord", "Paris", "75010", "20 rue La Fayette", "Île-de-France", "01 42 00 00 00", False),
    ("Ymmo Paris Sud", "Paris", "75014", "5 avenue du Maine", "Île-de-France", "01 43 00 00 00", False),
    ("Ymmo Bordeaux", "Bordeaux", "33000", "10 cours de l'Intendance", "Nouvelle-Aquitaine", "05 56 00 00 00", False),
    ("Ymmo Toulouse", "Toulouse", "31000", "15 rue d'Alsace-Lorraine", "Occitanie", "05 61 00 00 00", False),
    ("Ymmo Nice", "Nice", "06000", "30 Promenade des Anglais", "PACA", "04 93 00 00 00", False),
    ("Ymmo Nantes", "Nantes", "44000", "8 rue Crébillon", "Pays de la Loire", "02 40 00 00 00", False),
    ("Ymmo Strasbourg", "Strasbourg", "67000", "12 place Kléber", "Grand Est", "03 88 00 00 00", False),
    ("Ymmo Lille", "Lille", "59000", "20 rue de Béthune", "Hauts-de-France", "03 20 00 00 00", False),
    ("Ymmo Rennes", "Rennes", "35000", "5 rue Le Bastard", "Bretagne", "02 99 00 00 00", False),
    ("Ymmo Montpellier", "Montpellier", "34000", "10 rue de la Loge", "Occitanie", "04 67 00 00 00", False),
]

FIRST_NAMES = ["Léa", "Lucas", "Emma", "Hugo", "Chloé", "Louis", "Manon", "Théo",
               "Sarah", "Nathan", "Camille", "Tom", "Julie", "Antoine", "Marie",
               "Pierre", "Sophie", "Alexandre", "Laura", "Maxime", "Inès", "Adam"]
LAST_NAMES = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
              "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
              "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier"]

PROPERTY_TYPES = [
    ("APARTMENT", "Appartement"),
    ("HOUSE", "Maison"),
    ("LAND", "Terrain"),
    ("COMMERCIAL", "Local commercial"),
    ("OFFICE", "Bureau"),
]

DESCRIPTIONS = {
    "APARTMENT": [
        "Magnifique appartement lumineux avec vue dégagée. Cuisine équipée, salon spacieux et chambres parentales.",
        "Charmant appartement rénové dans un immeuble haussmannien. Parquet d'origine, hauteur sous plafond exceptionnelle.",
        "Appartement moderne avec balcon, idéalement situé près des commerces et transports.",
    ],
    "HOUSE": [
        "Belle maison familiale avec jardin paysager. Cuisine ouverte sur séjour cathédrale, 4 chambres dont une suite parentale.",
        "Maison de caractère entièrement rénovée. Pièces de réception traversantes, cheminée, beau jardin clos.",
        "Maison contemporaine avec piscine et terrain arboré. Belles prestations, prête à habiter.",
    ],
    "LAND": [
        "Terrain constructible plat dans secteur recherché. Viabilisé, exposition sud.",
        "Beau terrain de plus de 1000 m² avec vue dégagée. Possibilité de construire une grande maison.",
    ],
    "COMMERCIAL": [
        "Local commercial idéalement situé en cœur de ville. Grande vitrine, fort passage piétonnier.",
        "Boutique avec arrière-boutique, proche des transports. Idéal commerce de bouche ou activité libérale.",
    ],
    "OFFICE": [
        "Plateau de bureaux entièrement rénové. Climatisation, fibre optique, places de parking.",
        "Bureaux modulables en plein centre d'affaires. Visibilité optimale, accessibilité PMR.",
    ],
}

CITIES_LATLNG = {
    "Aix-en-Provence": (43.5263, 5.4454),
    "Marseille": (43.2965, 5.3698),
    "Lyon": (45.7640, 4.8357),
    "Paris": (48.8566, 2.3522),
    "Bordeaux": (44.8378, -0.5792),
    "Toulouse": (43.6047, 1.4442),
    "Nice": (43.7102, 7.2620),
    "Nantes": (47.2184, -1.5536),
    "Strasbourg": (48.5734, 7.7521),
    "Lille": (50.6292, 3.0573),
    "Rennes": (48.1173, -1.6778),
    "Montpellier": (43.6109, 3.8772),
}


class Command(BaseCommand):
    help = "Génère des données de démonstration pour Ymmo"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Supprime toutes les données existantes avant de seeder")
        parser.add_argument("--properties", type=int, default=200,
                            help="Nombre de biens à créer (défaut: 200)")

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)  # reproductibilité

        if options["reset"]:
            self.stdout.write(self.style.WARNING("Suppression des données existantes…"))
            Tx.objects.all().delete()
            VisitRequest.objects.all().delete()
            InfoRequest.objects.all().delete()
            FavoriteProperty.objects.all().delete()
            Property.objects.all().delete()
            Agency.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()

        # 1. Super-admin
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@ymmo.fr",
                "first_name": "Admin",
                "last_name": "Ymmo",
                "is_staff": True,
                "is_superuser": True,
                "role": User.Role.ADMIN,
            },
        )
        if created:
            admin.set_password("Admin12345!")
            admin.save()
            self.stdout.write(self.style.SUCCESS("✓ Super-admin créé : admin / Admin12345!"))

        # 2. Agences
        agencies = []
        for name, city, postal, addr, region, phone, is_hq in AGENCIES_DATA:
            lat, lng = CITIES_LATLNG.get(city, (None, None))
            agency, _ = Agency.objects.get_or_create(
                name=name,
                defaults={
                    "city": city, "postal_code": postal, "address": addr,
                    "region": region, "phone": phone,
                    "email": f"{city.lower().replace(' ', '').replace('-', '')}@ymmo.fr",
                    "is_headquarters": is_hq,
                    "latitude": lat, "longitude": lng,
                    "description": f"L'agence {name} vous accompagne dans tous vos projets immobiliers à {city} et alentours.",
                },
            )
            agencies.append(agency)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(agencies)} agences créées"))

        # 3. Agents (un par agence)
        agents = []
        for i, agency in enumerate(agencies):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            username = f"agent.{agency.city.lower().replace(' ', '').replace('-', '')}"
            agent, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@ymmo.fr",
                    "first_name": fn, "last_name": ln,
                    "phone": f"06 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}",
                    "role": User.Role.AGENT, "agency": agency,
                },
            )
            if created:
                agent.set_password("Agent12345!")
                agent.save()
            agents.append(agent)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(agents)} agents créés (mdp : Agent12345!)"))

        # 4. Clients
        clients = []
        for i in range(30):
            fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            username = f"client{i+1:02d}"
            client, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": fn, "last_name": ln,
                    "phone": f"06 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}",
                    "role": User.Role.CLIENT,
                    "city": random.choice([a.city for a in agencies]),
                },
            )
            if created:
                client.set_password("Client12345!")
                client.save()
            clients.append(client)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(clients)} clients créés (mdp : Client12345!)"))

        # 5. Biens
        nb = options["properties"]
        statuses = (
            [Property.Status.AVAILABLE] * 70
            + [Property.Status.UNDER_OFFER] * 10
            + [Property.Status.SOLD] * 15
            + [Property.Status.DRAFT] * 5
        )
        for i in range(nb):
            agency = random.choice(agencies)
            agent = next((a for a in agents if a.agency_id == agency.id), random.choice(agents))
            ptype, ptype_label = random.choice(PROPERTY_TYPES)
            transaction_type = random.choices(
                [Property.Transaction.SALE, Property.Transaction.RENT],
                weights=[80, 20],
            )[0]

            # Surface et prix dépendent du type
            if ptype == "APARTMENT":
                surface = random.randint(25, 200)
                rooms = max(1, surface // 25)
                base_price_sqm = random.randint(2500, 9000)
            elif ptype == "HOUSE":
                surface = random.randint(80, 350)
                rooms = max(3, surface // 30)
                base_price_sqm = random.randint(2000, 7000)
            elif ptype == "LAND":
                surface = random.randint(300, 3000)
                rooms = 0
                base_price_sqm = random.randint(80, 500)
            elif ptype == "COMMERCIAL":
                surface = random.randint(40, 400)
                rooms = max(1, surface // 50)
                base_price_sqm = random.randint(1500, 6000)
            else:  # OFFICE
                surface = random.randint(50, 500)
                rooms = max(2, surface // 40)
                base_price_sqm = random.randint(1800, 5500)

            price = surface * base_price_sqm
            if transaction_type == Property.Transaction.RENT:
                price = price * Decimal("0.005")  # ~0.5% du prix de vente / mois

            lat, lng = CITIES_LATLNG.get(agency.city, (None, None))
            if lat:
                lat += random.uniform(-0.05, 0.05)
                lng += random.uniform(-0.05, 0.05)

            status = random.choice(statuses)
            published_at = timezone.now() - timedelta(days=random.randint(0, 365)) if status != Property.Status.DRAFT else None

            prop = Property.objects.create(
                reference=f"YMM{i+1:05d}",
                title=f"{ptype_label} {surface} m² - {agency.city}",
                description=random.choice(DESCRIPTIONS.get(ptype, ["Bien immobilier."])),
                property_type=ptype,
                transaction_type=transaction_type,
                status=status,
                is_featured=(random.random() < 0.05),
                surface=surface,
                land_surface=random.randint(200, 2000) if ptype == "HOUSE" else None,
                rooms=rooms,
                bedrooms=max(0, rooms - 2) if rooms > 1 else 0,
                bathrooms=random.randint(1, 3) if rooms > 1 else 0,
                floor=random.randint(0, 8) if ptype == "APARTMENT" else None,
                has_garage=random.random() < 0.4,
                has_garden=random.random() < 0.3 and ptype in ("HOUSE", "APARTMENT"),
                has_pool=random.random() < 0.1 and ptype == "HOUSE",
                has_balcony=random.random() < 0.5 and ptype == "APARTMENT",
                has_elevator=random.random() < 0.6 and ptype == "APARTMENT",
                is_furnished=random.random() < 0.2,
                energy_class=random.choice(["A", "B", "C", "D", "E"]),
                construction_year=random.randint(1950, 2024),
                price=Decimal(price).quantize(Decimal("0.01")),
                monthly_charges=Decimal(random.randint(20, 300)) if ptype == "APARTMENT" else None,
                agency_fees_percent=Decimal("4.00"),
                address=f"{random.randint(1, 200)} {random.choice(['rue', 'avenue', 'boulevard', 'place'])} {random.choice(LAST_NAMES)}",
                city=agency.city,
                postal_code=agency.postal_code,
                region=agency.region,
                latitude=lat, longitude=lng,
                agency=agency,
                agent=agent,
                views_count=random.randint(0, 5000) if status == Property.Status.AVAILABLE else 0,
                published_at=published_at,
            )

        self.stdout.write(self.style.SUCCESS(f"✓ {nb} biens créés"))

        # 6. Demandes de visite (30)
        available = list(Property.objects.filter(status=Property.Status.AVAILABLE)[:50])
        for _ in range(30):
            client = random.choice(clients)
            prop = random.choice(available)
            VisitRequest.objects.create(
                property=prop,
                client=client,
                full_name=client.get_full_name(),
                email=client.email,
                phone=client.phone,
                preferred_date=date.today() + timedelta(days=random.randint(1, 21)),
                message=random.choice([
                    "Merci de me confirmer la visite.",
                    "Disponible en semaine après 18h.",
                    "Pouvez-vous m'envoyer la fiche DPE ?",
                    "",
                ]),
                status=random.choice([
                    VisitRequest.Status.PENDING,
                    VisitRequest.Status.CONFIRMED,
                    VisitRequest.Status.DONE,
                ]),
            )
        self.stdout.write(self.style.SUCCESS("✓ 30 demandes de visite créées"))

        # 7. Demandes d'info (15)
        for _ in range(15):
            client = random.choice(clients)
            prop = random.choice(available)
            InfoRequest.objects.create(
                property=prop, client=client,
                full_name=client.get_full_name(),
                email=client.email, phone=client.phone,
                question=random.choice([
                    "Le prix est-il négociable ?",
                    "Quelle est la taxe foncière ?",
                    "Le bien est-il toujours disponible ?",
                ]),
            )
        self.stdout.write(self.style.SUCCESS("✓ 15 demandes d'info créées"))

        # 8. Transactions (10 actives + 5 signées)
        for i in range(15):
            prop = random.choice(available)
            buyer = random.choice(clients)
            agent_for = next((a for a in agents if a.agency_id == prop.agency_id), random.choice(agents))
            offer_price = prop.price * Decimal(random.uniform(0.92, 1.0))

            status = (random.choice([
                Tx.Status.OFFER_MADE, Tx.Status.OFFER_ACCEPTED,
                Tx.Status.COMPROMISE, Tx.Status.FINANCING,
            ]) if i < 10 else Tx.Status.SIGNED)

            tx = Tx.objects.create(
                reference=f"TX{i+1:04d}",
                property=prop,
                type=Tx.Type.SALE,
                status=status,
                buyer=buyer,
                agent=agent_for,
                offer_price=offer_price.quantize(Decimal("0.01")),
                final_price=offer_price.quantize(Decimal("0.01")) if status == Tx.Status.SIGNED else None,
                agency_commission=(offer_price * Decimal("0.04")).quantize(Decimal("0.01")),
                offer_date=date.today() - timedelta(days=random.randint(5, 90)),
                expected_signature_date=date.today() + timedelta(days=random.randint(15, 60)),
                signed_at=timezone.now() if status == Tx.Status.SIGNED else None,
            )

            # Quelques étapes
            steps = [
                ("Offre déposée", "L'acheteur a déposé une offre.", True),
                ("Offre acceptée", "Le vendeur a accepté l'offre.", status != Tx.Status.OFFER_MADE),
                ("Compromis signé", "Compromis de vente signé chez le notaire.",
                 status in (Tx.Status.COMPROMISE, Tx.Status.FINANCING, Tx.Status.SIGNED)),
                ("Acte définitif", "Acte authentique signé.", status == Tx.Status.SIGNED),
            ]
            for title, desc, done in steps:
                TransactionStep.objects.create(
                    transaction=tx, title=title, description=desc,
                    is_completed=done,
                    completed_at=timezone.now() if done else None,
                )

        self.stdout.write(self.style.SUCCESS("✓ 15 transactions créées"))

        # 9. Quelques favoris
        for client in random.sample(clients, 20):
            for prop in random.sample(available, random.randint(1, 5)):
                FavoriteProperty.objects.get_or_create(user=client, property=prop)

        self.stdout.write(self.style.SUCCESS(
            "\n🎉 Seed terminé !\n"
            "Comptes de test :\n"
            "  • admin / Admin12345!  (super-admin)\n"
            "  • agent.marseille / Agent12345!  (agent)\n"
            "  • client01 / Client12345!  (client)\n"
        ))
