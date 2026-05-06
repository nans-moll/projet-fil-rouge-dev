# Ymmo — Plateforme immobilière

> Projet fil rouge B2 Ynov — UF INFRA & DEV
> **Partie DEV** : plateforme web Django pour le groupe immobilier Ymmo
> (siège Aix-en-Provence + 12 agences en France).

---

## ✨ Fonctionnalités

### Visiteurs et clients
- 🔍 Recherche multi-critères de biens (ville, prix, surface, équipements)
- 🏠 Fiche détaillée avec galerie, caractéristiques, biens similaires
- 📅 Demande de visite et d'informations en ligne
- ❤ Favoris (clients connectés)
- 👤 Espace client : suivi des démarches, dossiers de transaction, timeline

### Agents immobiliers
- 📦 CRUD complet des biens de leur agence
- 🖼 Upload photos avec gestion de la photo principale
- 📨 Traitement des demandes de visite (statut, date, notes)
- 💼 Gestion des transactions avec timeline d'étapes
- 📊 Tableau de bord avec KPIs

### Direction / admin
- 📈 Dashboard analytics : KPIs, top villes, tendances, biens populaires
- 🛠 Django Admin complet
- 📒 Notebook Jupyter pour analyses approfondies (Pandas + scikit-learn)

---

## 🛠 Stack technique

- **Backend** : Python 3.11+ / Django 5
- **Frontend** : Django Templates + Tailwind CSS + Alpine.js + Chart.js
- **BDD** : SQLite (dev) / MySQL ou PostgreSQL (prod)
- **Analyse** : Pandas, NumPy, Matplotlib, scikit-learn, Jupyter
- **Auth** : Django Auth + backend custom (login email ou username)

---

## 🚀 Installation

### 1. Pré-requis
- Python 3.11+
- pip

### 2. Cloner et préparer l'environnement

```powershell
# Windows PowerShell
cd "C:\Users\PLUTO\Desktop\projet fil rouge"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

```bash
# Linux/macOS
cd "projet fil rouge"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac
```

Éditer `.env` si nécessaire (par défaut SQLite, mode debug).

### 4. Initialiser la base

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
```

La commande `seed_demo` crée :
- 1 super-admin
- 13 agences (1 siège + 12 antennes)
- 13 agents (1 par agence)
- 30 clients
- ~200 biens immobiliers
- Demandes de visite, transactions, favoris

### 5. Lancer le serveur

```bash
python manage.py runserver
```

Ouvrir **http://localhost:8000**.

---

## 🔑 Comptes de démonstration

| Rôle | Identifiant | Mot de passe | Accès |
|------|-------------|--------------|-------|
| Super-admin | `admin` | `Admin12345!` | tout + `/admin/` |
| Agent | `agent.marseille` (et 12 autres) | `Agent12345!` | `/transactions/agent/` |
| Client | `client01` à `client30` | `Client12345!` | `/transactions/mon-espace/` |

L'identifiant peut être l'email ou le username.

---

## 📊 Notebook d'analyse de données

```bash
jupyter notebook notebooks/market_analysis.ipynb
```

Le notebook charge les données via l'ORM Django et produit :
1. Tendances par ville (volume, prix moyen, prix au m²)
2. Répartition par type de bien
3. Identification des biens populaires
4. **Modèle de prédiction de prix** (régression linéaire vs Random Forest)
5. **Cartographie des opportunités d'achat** (zones avec prix bas + forte demande)

---

## 🧪 Lancer les tests

```bash
pytest
```

---

## 📁 Structure du projet

```
projet fil rouge/
├── manage.py
├── requirements.txt
├── README.md
├── config/                  # Configuration Django (settings, URLs, WSGI)
├── apps/                    # Apps métier
│   ├── core/                # Pages publiques + contact
│   ├── accounts/            # User custom + auth + rôles
│   ├── properties/          # Agences, biens, photos, favoris
│   ├── transactions/        # Visites, demandes, transactions
│   └── analytics/           # Dashboard analytics
├── templates/               # Templates HTML (Tailwind)
├── static/                  # Assets statiques
├── media/                   # Photos uploadées
├── notebooks/
│   └── market_analysis.ipynb
└── docs/
    ├── 01_documentation_fonctionnelle.md
    └── 02_documentation_technique.md
```

---

## 📚 Documentation

- **Fonctionnelle** : [`docs/01_documentation_fonctionnelle.md`](docs/01_documentation_fonctionnelle.md) — cas d'usage, règles métier, personas
- **Technique** : [`docs/02_documentation_technique.md`](docs/02_documentation_technique.md) — archi, BDD, sécurité, déploiement

---

## ✅ Critères de la grille DEV (oral final)

| Critère | Pondération | Où c'est traité |
|---------|-------------|-----------------|
| Solution répondant au besoin métier | 5 | Plateforme complète + dashboards par rôle |
| App fonctionnelle complète | 10 | Auth, CRUD biens, transactions, demandes, espace client/agent |
| Bonnes pratiques SOLID/DRY/KISS | 3 | `TimestampedModel`, services, mixins, template `_card.html` |
| POO avancée | 3 | Hiérarchie de mixins, classes abstraites, `@property`, méthodes utilitaires |
| Modèle relationnel | 3 | 9 modèles, relations 1-N et N-N, contraintes (PROTECT/CASCADE/SET_NULL) |
| Requêtes SQL | 4 | `select_related`, `prefetch_related`, `annotate`, `Avg`, `Count`, `F`, indexes |
| UI intuitive | 5 | Tailwind, navigation claire, breadcrumb, CTA visibles |
| Responsive + a11y WCAG | 3 | Mobile-first, skip-link, ARIA, contrastes, focus visible |

---

## 🤝 Équipe

Projet réalisé par 2 étudiants en B2 Ynov Informatique.

---

## 📝 Licence

Projet académique — tous droits réservés.
