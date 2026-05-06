"""
Télécharge des photos d'immobilier (maisons / appartements uniquement)
depuis loremflickr.com et garantit que chaque photo est unique
(détection de doublons par hash MD5 du contenu).

Quel que soit le type du bien (maison, appart, terrain, local, bureau),
les photos seront toujours des intérieurs / extérieurs résidentiels.

Usage :
    python manage.py add_photos                         # 4 photos / 100 biens
    python manage.py add_photos --per-property=5
    python manage.py add_photos --reset                 # remplace les photos existantes
    python manage.py add_photos --limit=200
"""
import hashlib
import random

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.properties.models import Property, PropertyImage


# Tags loremflickr pour maisons & appartements UNIQUEMENT.
# 1re photo = extérieur ; suivantes = intérieurs variés.
HOUSE_TAGS = [
    "house,home,villa,exterior",          # Façade
    "livingroom,interior,modern,home",    # Salon
    "kitchen,modern,interior,house",      # Cuisine
    "bedroom,interior,home,cosy",         # Chambre
    "bathroom,interior,modern,home",      # Salle de bain
    "garden,backyard,terrace,house",      # Jardin
    "diningroom,interior,modern",         # Salle à manger
]

APARTMENT_TAGS = [
    "apartment,building,facade,city",        # Immeuble
    "livingroom,interior,modern,apartment",  # Salon
    "kitchen,interior,modern,apartment",     # Cuisine
    "bedroom,interior,apartment,modern",     # Chambre
    "bathroom,interior,modern,apartment",    # Salle de bain
    "balcony,view,city,apartment",           # Balcon / vue
    "loft,interior,modern,studio",           # Loft / studio
]


class Command(BaseCommand):
    help = "Télécharge des photos uniques de maisons/appartements pour chaque bien."

    def add_arguments(self, parser):
        parser.add_argument("--per-property", type=int, default=4)
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--width", type=int, default=1200)
        parser.add_argument("--height", type=int, default=800)
        parser.add_argument("--max-retry", type=int, default=4,
                            help="Tentatives par photo si doublon")

    def handle(self, *args, **options):
        if options["reset"]:
            count = PropertyImage.objects.count()
            for img in PropertyImage.objects.all():
                img.image.delete(save=False)
            PropertyImage.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Suppression de {count} photos existantes."))

        per_prop = options["per_property"]
        limit = options["limit"]
        w, h = options["width"], options["height"]
        max_retry = options["max_retry"]

        properties = Property.objects.filter(
            status__in=[Property.Status.AVAILABLE, Property.Status.UNDER_OFFER]
        ).order_by("-is_featured", "-published_at")[:limit]

        total = properties.count()
        self.stdout.write(
            f"Téléchargement de ~{per_prop * total} photos uniques pour {total} biens "
            f"(maisons & appartements seulement)…"
        )

        seen_hashes = set()  # garantit l'unicité des contenus
        ok, fail, dups_avoided = 0, 0, 0
        lock_counter = 1  # incrément global pour varier les requêtes

        for i, prop in enumerate(properties, start=1):
            if prop.photos.exists() and not options["reset"]:
                continue

            # Choix : si APARTMENT → tags appart, sinon → tags maison
            # (les autres types reçoivent des photos résidentielles type maison)
            tags_list = (
                APARTMENT_TAGS if prop.property_type == "APARTMENT"
                else HOUSE_TAGS
            )

            for j in range(per_prop):
                tags = tags_list[j % len(tags_list)]
                content = None

                # Retry tant qu'on tombe sur un doublon (ou échec réseau)
                for attempt in range(max_retry):
                    lock_counter += 1
                    salt = random.randint(1, 999999)
                    url = f"https://loremflickr.com/{w}/{h}/{tags}?lock={lock_counter}{salt}"
                    try:
                        r = requests.get(url, timeout=20, allow_redirects=True)
                        r.raise_for_status()
                        if not r.content or len(r.content) < 1500:
                            continue
                        h_md5 = hashlib.md5(r.content).hexdigest()
                        if h_md5 in seen_hashes:
                            dups_avoided += 1
                            continue  # doublon → retry
                        seen_hashes.add(h_md5)
                        content = r.content
                        break
                    except Exception:
                        continue

                if content is None:
                    fail += 1
                    self.stdout.write(self.style.WARNING(
                        f"  ⚠ {prop.reference}/{j} : échec après {max_retry} tentatives"
                    ))
                    continue

                img = PropertyImage(
                    property=prop, is_main=(j == 0), order=j,
                    caption=tags.split(",")[0].title(),
                )
                img.image.save(
                    f"{prop.reference}_{j}.jpg",
                    ContentFile(content),
                    save=True,
                )
                ok += 1

            if i % 10 == 0:
                self.stdout.write(
                    f"  ... {i}/{total} biens — {ok} photos OK, "
                    f"{dups_avoided} doublons évités, {fail} échecs"
                )

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Terminé : {ok} photos uniques téléchargées, "
            f"{dups_avoided} doublons évités, {fail} échecs."
        ))
