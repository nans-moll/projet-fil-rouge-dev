# Documentation technique — Ymmo

---

## 1. Architecture générale

```
┌───────────────────────────────────────────────────────────────┐
│                         CLIENT (navigateur)                    │
│   HTML5 + Tailwind CSS + Alpine.js + Chart.js (CDN)            │
└───────────────────────────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                      DJANGO 5 (backend)                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ URL routing (config/urls.py)                            │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Vues (CBV/FBV) — apps/{core,accounts,properties,        │  │
│  │                       transactions,analytics}/views.py  │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ Couche service (apps/properties/services.py …)          │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ ORM Django — modèles dans apps/*/models.py              │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                BASE DE DONNÉES — MySQL ou PostgreSQL          │
│                  (SQLite par défaut en dev)                    │
└───────────────────────────────────────────────────────────────┘

       ┌───────────────────────────────────────┐
       │  Notebook Jupyter (analyse offline)   │
       │  pandas + scikit-learn → ORM Django   │
       └───────────────────────────────────────┘
```

---

## 2. Stack technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| Langage backend | Python | 3.11+ |
| Framework web | Django | 5.0 |
| ORM | Django ORM | inclus |
| Templates | Django Templates + Tailwind CSS (CDN) + Alpine.js | — |
| API REST | Django REST Framework (extensible) | 3.15 |
| BDD (dev) | SQLite | — |
| BDD (prod) | MySQL 8 ou PostgreSQL 16 | — |
| Auth | Django auth + backend custom email/username | — |
| Tests | pytest-django | 4.8 |
| Analyse | Pandas, NumPy, Matplotlib, scikit-learn, Jupyter | — |
| Versionning | Git + GitHub | — |

---

## 3. Structure du projet

```
projet fil rouge/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── config/                      # Configuration projet
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                        # Apps métier
│   ├── core/                    # Pages publiques + contact
│   ├── accounts/                # User custom + auth + rôles
│   ├── properties/              # Agences, biens, photos, favoris
│   ├── transactions/            # Visites, demandes, transactions
│   └── analytics/               # Snapshots + dashboard analytics
├── templates/                   # Templates Django partagés
│   ├── base.html
│   ├── core/
│   ├── accounts/
│   ├── properties/
│   ├── transactions/
│   └── analytics/
├── static/                      # Assets statiques
├── media/                       # Uploads (photos)
├── notebooks/
│   └── market_analysis.ipynb    # Analyse Pandas + ML
└── docs/
    ├── 01_documentation_fonctionnelle.md
    └── 02_documentation_technique.md
```

---

## 4. Modèle de données

### 4.1 Diagramme entité-relation (textuel)

```
User (accounts)
 ├─ role: ADMIN | AGENT | CLIENT
 ├─ agency → Agency           (si AGENT)
 └─ favorites ↔ Property       (M2M via FavoriteProperty)

Agency (properties)
 ├─ is_headquarters
 ├─ city, postal_code, address
 └─ properties → Property[]

Property (properties)
 ├─ reference (unique)
 ├─ property_type, transaction_type, status
 ├─ surface, rooms, price, energy_class…
 ├─ agency → Agency           (PROTECT)
 ├─ agent → User              (SET_NULL)
 ├─ seller → User             (SET_NULL)
 └─ photos → PropertyImage[]

PropertyImage (properties)
 └─ property → Property        (CASCADE)

VisitRequest (transactions)
 ├─ property → Property        (CASCADE)
 ├─ client → User              (SET_NULL, peut être null)
 └─ status: PENDING|CONFIRMED|DONE|CANCELLED

InfoRequest (transactions)
 └─ property → Property        (CASCADE)

Transaction (transactions)
 ├─ reference (unique)
 ├─ status: OFFER_MADE → … → SIGNED
 ├─ property → Property        (PROTECT)
 ├─ buyer / seller / agent → User
 └─ steps → TransactionStep[]

TransactionStep (transactions)
 └─ transaction → Transaction  (CASCADE)

ContactMessage (core)
MarketSnapshot (analytics)
```

### 4.2 Choix techniques de modélisation

- **`TimestampedModel`** : classe abstraite mutualisant `created_at` / `updated_at` (DRY).
- **Suppression** :
  - `PROTECT` sur `Property → Agency` (ne pas perdre l'historique en supprimant une agence)
  - `CASCADE` sur `PropertyImage → Property` (les photos disparaissent avec le bien)
  - `SET_NULL` sur `Property → agent / seller` (préserver les biens si l'utilisateur est supprimé)
- **Index** sur `Property` : `(status, transaction_type)`, `city`, `price`, `property_type`.
- **`unique_together`** sur `FavoriteProperty(user, property)` pour éviter les doublons.

### 4.3 Schéma SQL principal (extrait simplifié)

```sql
CREATE TABLE accounts_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254),
    role ENUM('ADMIN', 'AGENT', 'CLIENT') DEFAULT 'CLIENT',
    agency_id BIGINT NULL REFERENCES properties_agency(id) ON DELETE SET NULL,
    -- ... champs Django auth + champs custom
);

CREATE TABLE properties_agency (
    id BIGINT PRIMARY KEY,
    name VARCHAR(120) UNIQUE,
    slug VARCHAR(140) UNIQUE,
    is_headquarters BOOLEAN DEFAULT FALSE,
    city VARCHAR(100),
    postal_code VARCHAR(10),
    -- ...
);

CREATE TABLE properties_property (
    id BIGINT PRIMARY KEY,
    reference VARCHAR(20) UNIQUE,
    title VARCHAR(200),
    slug VARCHAR(220) UNIQUE,
    property_type VARCHAR(15),
    transaction_type VARCHAR(10),
    status VARCHAR(15),
    surface INT UNSIGNED,
    price DECIMAL(12,2),
    city VARCHAR(100),
    agency_id BIGINT REFERENCES properties_agency(id) ON DELETE RESTRICT,
    agent_id BIGINT REFERENCES accounts_user(id) ON DELETE SET NULL,
    -- ...
    INDEX idx_status_transaction (status, transaction_type),
    INDEX idx_city (city),
    INDEX idx_price (price)
);
```

(Le SQL complet est généré automatiquement par les migrations Django — voir `python manage.py sqlmigrate`.)

---

## 5. Application des principes SOLID, DRY, KISS

| Principe | Application |
|----------|-------------|
| **SRP** (Single Responsibility) | Chaque classe a une responsabilité : `User` = identité+rôle, `Property` = bien, `PropertySearchService` = logique de recherche. Les **vues** orchestrent, les **services** font la logique métier, les **modèles** portent les données + invariants. |
| **OCP** (Open/Closed) | `RoleRequiredMixin` extensible (`AgentRequiredMixin`, `ClientRequiredMixin`, `AdminRequiredMixin`) sans toucher au mixin parent. |
| **LSP** | Tous les *required mixins* respectent le contrat de `RoleRequiredMixin`. |
| **ISP** | Forms séparés pour l'inscription publique (`ClientRegisterForm`) vs le profil (`ProfileForm`) — pas de surface inutile. |
| **DIP** | Le notebook Python dépend de l'**ORM Django**, pas du SQL ; le service `PropertySearchService` dépend de `Property` mais pas des vues. |
| **DRY** | `TimestampedModel` (created_at/updated_at), template `_card.html` réutilisé partout (home, liste, similaires, agence). |
| **KISS** | Pas d'over-engineering : pas d'API REST publique au démarrage (mais DRF prêt si besoin), pas de Celery pour les emails (backend console en dev), pas de microservices. |

---

## 6. Sécurité

| Mécanisme | Configuration |
|-----------|---------------|
| **CSRF** | Activé par défaut (middleware Django). |
| **Sessions** | `SESSION_COOKIE_HTTPONLY=True`, `SAMESITE=Lax`. |
| **HSTS / SSL** | Activés en prod (`DEBUG=False`). |
| **Mot de passe** | Min 10 chars + validators Django (similarité, courant, numérique). |
| **Rôles** | `RoleRequiredMixin` + `@role_required` côté vue. |
| **Auth** | Backend custom email-or-username (`apps/accounts/backends.py`). |
| **XSS** | Auto-escape Django sur tous les templates. |
| **Clickjacking** | `X_FRAME_OPTIONS=DENY`. |
| **Upload** | `FileField`/`ImageField` avec `upload_to` paramétré, taille max via `DATA_UPLOAD_MAX_MEMORY_SIZE`. |
| **Querysets** | Utilisation systématique des paramètres ORM (pas de SQL string). |

---

## 7. Performance

- **`select_related`** : sur toutes les FK utilisées dans les listes (`agency`, `agent`, `buyer`).
- **`prefetch_related`** : sur les `photos` (M2M / reverse FK).
- **Index DB** : ajoutés sur les colonnes filtrables.
- **Pagination** : `paginate_by=12` sur les listes de biens.
- **Lazy loading** images : attribut `loading="lazy"` HTML5.
- **Compteur de vues** : update atomique via `F("views_count") + 1`.
- **Template fragments** : `_card.html` mutualisé (DRY + cache friendly).

---

## 8. Accessibilité (WCAG 2.1 AA)

- **Skip link** « Aller au contenu principal » (cf. `templates/base.html`).
- **Focus visible** custom (`:focus-visible { outline: 3px solid #f59e0b; }`).
- **Contrastes** : combinaisons primary/blanc et accent/blanc validées AA.
- **Sémantique** : `<main>`, `<nav>`, `<header>`, `<footer>`, `<article>`, `<section>`, `<aside>`.
- **ARIA** : `aria-label`, `aria-labelledby`, `aria-controls`, `aria-expanded`, `role="search"`, `role="status"`.
- **Formulaires** : tous les champs ont un `<label>` associé via `for`.
- **Images** : `alt` systématique (vide pour décoratif, descriptif sinon).
- **Responsive** : `meta viewport` + breakpoints Tailwind `sm/md/lg/xl`.

---

## 9. URLs et endpoints

### 9.1 Pages publiques
| URL | Vue | Rôle requis |
|-----|-----|-------------|
| `/` | `HomeView` | — |
| `/biens/` | `PropertyListView` | — |
| `/biens/<slug>/` | `PropertyDetailView` | — |
| `/biens/agence/<slug>/` | `AgencyDetailView` | — |
| `/agences/` | `AgenciesView` | — |
| `/contact/` | `ContactView` | — |
| `/a-propos/` | `AboutView` | — |

### 9.2 Auth
| URL | Vue |
|-----|-----|
| `/comptes/connexion/` | `CustomLoginView` |
| `/comptes/inscription/` | `RegisterView` |
| `/comptes/deconnexion/` | `CustomLogoutView` |
| `/comptes/profil/` | `ProfileView` |
| `/comptes/mot-de-passe/...` | flow reset Django |

### 9.3 Espace client
| URL | Rôle |
|-----|------|
| `/transactions/mon-espace/` | CLIENT |
| `/transactions/mon-espace/dossier/<id>/` | CLIENT |
| `/biens/favori/<id>/` | CLIENT |
| `/transactions/bien/<id>/visite/` | tout le monde |
| `/transactions/bien/<id>/info/` | tout le monde |

### 9.4 Espace agent / admin
| URL | Rôle |
|-----|------|
| `/transactions/agent/` | AGENT/ADMIN |
| `/biens/gestion/` | AGENT/ADMIN |
| `/biens/gestion/nouveau/` | AGENT/ADMIN |
| `/biens/gestion/<id>/modifier/` | AGENT/ADMIN |
| `/biens/gestion/<id>/supprimer/` | AGENT/ADMIN |
| `/transactions/agent/visites/` | AGENT/ADMIN |
| `/transactions/agent/transactions/` | AGENT/ADMIN |
| `/analytics/` | AGENT/ADMIN |
| `/admin/` | ADMIN (Django Admin) |

---

## 10. Déploiement

### 10.1 Environnements
| Env | BDD | Debug | Static |
|-----|-----|-------|--------|
| dev | SQLite | True | dev server |
| staging | MySQL | False | WhiteNoise / nginx |
| prod | MySQL/PostgreSQL | False | nginx + CDN |

### 10.2 Procédure (résumé)
```bash
# 1. Cloner
git clone <repo>
cd "projet fil rouge"

# 2. Virtualenv
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 3. Dépendances
pip install -r requirements.txt

# 4. Configuration
copy .env.example .env
# (éditer .env si besoin)

# 5. Migrations + seed
python manage.py migrate
python manage.py seed_demo

# 6. Lancer le serveur
python manage.py runserver
# → http://localhost:8000

# 7. (Optionnel) Notebook Jupyter
jupyter notebook notebooks/market_analysis.ipynb
```

### 10.3 Déploiement prod (esquisse)
- Reverse proxy nginx (TLS, gzip, headers sécu).
- Gunicorn (ou Uvicorn + ASGI) en service systemd.
- BDD MySQL/PostgreSQL managée (siège ou cloud).
- Static via `collectstatic` + WhiteNoise ou CDN.
- Sauvegardes : `mysqldump` / `pg_dump` quotidien.

---

## 11. Tests

Stratégie :
- **Unitaires** : services (`PropertySearchService`), méthodes de modèle (`Property.price_per_sqm`).
- **Intégration** : vues principales (login, création de bien, demande de visite).
- **Smoke tests** : vérifie qu'aucune URL ne renvoie de 500.

Lancer : `pytest`

---

## 12. Évolutions prévues

| Item | Priorité |
|------|----------|
| API REST DRF complète (mobile, partenaires) | 🔵 Moyen |
| Notifications email (Celery + Redis) | 🔵 Moyen |
| Carte interactive Leaflet/Mapbox | 🟢 Bas |
| Signature électronique (DocuSign / Yousign) | 🟢 Bas |
| Recherche full-text PostgreSQL ou ElasticSearch | 🔵 Moyen |
| Import DVF (open data prix immo France) pour enrichir les analyses | 🟢 Bas |
