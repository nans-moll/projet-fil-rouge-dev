# Documentation fonctionnelle — Ymmo

> Plateforme web centralisée d'achat / vente / location de biens immobiliers
> pour le groupe Ymmo (siège Aix-en-Provence + 12 agences).

---

## 1. Contexte et objectifs

### 1.1 Contexte
Le groupe Ymmo, implanté à Aix-en-Provence, dispose de 12 agences en France et
souhaite digitaliser ses opérations. La plateforme cible :
- les **clients** (acheteurs / vendeurs / locataires) ;
- les **agents** des 12 agences ;
- la **direction** (vue consolidée + analytics).

### 1.2 Objectifs métier
| # | Objectif | Critère de succès |
|---|----------|-------------------|
| O1 | Centraliser le catalogue de biens des 12 agences | 100% des biens dans le système |
| O2 | Permettre aux clients de chercher / réserver une visite en ligne | Réduction des appels téléphoniques |
| O3 | Suivre les transactions (offre → signature) | Délai moyen de signature mesurable |
| O4 | Outils d'analyse de marché et aide à la décision | Dashboard direction opérationnel |
| O5 | Gérer 3 rôles distincts (admin, agent, client) | Cloisonnement strict des accès |

---

## 2. Acteurs et rôles

| Rôle | Description | Périmètre d'accès |
|------|-------------|-------------------|
| **Admin** (direction) | Direction Ymmo | Vue globale + administration Django |
| **Agent** | Commercial d'une agence | CRUD biens + clients de son agence |
| **Client** | Acheteur / vendeur | Catalogue public + son espace personnel |
| **Visiteur** | Anonyme | Catalogue public + demandes (avec email) |

---

## 3. Cas d'usage principaux

### 3.1 Côté client / visiteur

#### UC-01 : Rechercher un bien
- **Acteur** : visiteur ou client
- **Pré-conditions** : aucune
- **Scénario** :
  1. L'utilisateur arrive sur la page d'accueil.
  2. Il saisit ville, type de transaction et budget dans la barre de recherche.
  3. Le système affiche les biens correspondants paginés.
  4. Il peut affiner avec les filtres (surface, pièces, équipements).
- **Post-condition** : liste de résultats triable (prix ↑↓, surface, date).

#### UC-02 : Consulter la fiche détaillée d'un bien
- **Scénario** :
  1. Clic sur une carte de bien.
  2. Affichage : galerie photos, caractéristiques, prix, localisation, biens similaires.
  3. CTA visibles : « Demander une visite », « Demander des informations ».

#### UC-03 : Demander une visite
- **Pré-conditions** : aucune (formulaire ouvert aux visiteurs).
- **Scénario** :
  1. Sur la fiche du bien, clic « Demander une visite ».
  2. Saisie nom, email, téléphone, date/heure souhaitée, message optionnel.
  3. Validation → demande créée avec statut « En attente ».
  4. L'agent référent reçoit la notification dans son tableau de bord.
- **Post-condition** : `VisitRequest` créée, statut `PENDING`.

#### UC-04 : S'inscrire / se connecter
- **Scénario** :
  1. Clic « Créer un compte ».
  2. Saisie infos personnelles + mot de passe.
  3. Validation → compte créé avec rôle `CLIENT`, connexion automatique.

#### UC-05 : Suivre ses démarches (espace client)
- **Pré-conditions** : être connecté en tant que client.
- **Affichage** :
  - Demandes de visite (statut, date, bien)
  - Demandes d'informations
  - Transactions en cours (avec barre de progression)
  - Favoris
- **Détail d'un dossier** : timeline d'étapes, statut, agent référent.

### 3.2 Côté agent

#### UC-10 : Gérer son catalogue de biens
- **Pré-conditions** : être connecté en tant qu'agent (ou admin).
- **Actions** :
  - Liste paginée des biens de son agence.
  - Création d'un bien (formulaire complet : caractéristiques, prix, localisation).
  - Modification, suppression, publication.
  - Upload multiple de photos avec photo principale.
- **Règle métier** : un agent ne voit que les biens de son agence (sauf admin).

#### UC-11 : Traiter une demande de visite
- **Scénario** :
  1. L'agent voit la demande dans son dashboard.
  2. Il l'ouvre et la met à jour : statut (`PENDING` → `CONFIRMED` → `DONE`), date confirmée, notes.
  3. Le client voit la mise à jour dans son espace.

#### UC-12 : Suivre une transaction
- **Cycle** : `OFFER_MADE` → `OFFER_ACCEPTED` → `COMPROMISE` → `FINANCING` → `SIGNED`.
- L'agent ajoute des étapes (visibles ou internes) qui s'affichent dans la timeline du client.
- Le système calcule un % d'avancement.

### 3.3 Côté direction (admin)

#### UC-20 : Tableau de bord analytics
- KPIs : annonces actives, biens vendus, prix moyen, vues totales.
- Graphiques : transactions / 12 mois, répartition par type.
- Top 10 villes (volume, prix moyen).
- Biens populaires (les plus vus).
- Renvoi vers le notebook Jupyter pour analyses approfondies.

#### UC-21 : Administration globale
Via Django Admin (`/admin/`) — tous les modèles, gestion des utilisateurs, agences,
biens, transactions, messages de contact.

---

## 4. Règles métier

| RM-01 | Un agent appartient à **une seule** agence. |
| RM-02 | Un bien est **rattaché à une agence**. Seul l'agent de cette agence (ou un admin) peut l'éditer. |
| RM-03 | Le prix d'un bien doit être > 0. |
| RM-04 | Un bien ne peut être affiché publiquement que si son statut est `AVAILABLE` ou `UNDER_OFFER`. |
| RM-05 | Une demande de visite peut être faite **avec ou sans compte** (champs nom/email obligatoires). |
| RM-06 | Un client ne voit que **ses propres** demandes et transactions. |
| RM-07 | Frais d'agence : 4% par défaut, ajustable par bien. |
| RM-08 | Une étape de transaction `visible_to_client = False` reste interne (notes agent). |

---

## 5. Parcours utilisateur (user stories)

### Persona 1 — Léa, jeune cadre cherchant à acheter
> *« En tant qu'acheteuse, je veux voir tous les T3 de moins de 350 000 € à Lyon, mettre mes coups de cœur en favoris, et planifier des visites en quelques clics. »*

Parcours :
1. Accueil → recherche « Lyon » + budget max → liste filtrée
2. Fiche bien → ajout aux favoris (création de compte au passage)
3. Demande de visite avec date proposée
4. Espace personnel → suivi du statut

### Persona 2 — Marc, agent à Marseille
> *« En tant qu'agent, je veux ajouter mes nouveaux mandats rapidement, traiter les demandes entrantes et voir mes performances. »*

Parcours :
1. Connexion → dashboard agent
2. Création d'un nouveau bien (formulaire structuré, upload photos)
3. Traitement d'une demande de visite (confirmation date)
4. Création d'une transaction lorsqu'une offre est faite
5. Mise à jour des étapes au fil du dossier

### Persona 3 — Sophie, directrice opérationnelle
> *« En tant que direction, je veux voir l'évolution du marché, les zones à fort potentiel et anticiper les tendances. »*

Parcours :
1. Connexion (admin) → dashboard analytics
2. Lecture des KPIs et des top villes
3. Ouverture du notebook Jupyter pour les analyses approfondies (prédictions, opportunités)

---

## 6. Maquettes (descriptions)

> Les maquettes haute fidélité sont implémentées directement en HTML/CSS dans
> les templates (cf. `templates/`). Voici le découpage :

| Page | Template | Wireframe |
|------|----------|-----------|
| Accueil | `templates/core/home.html` | Hero + recherche + KPIs + biens à la une + CTA |
| Liste biens | `templates/properties/list.html` | Sidebar filtres + grille 3 colonnes + pagination |
| Fiche bien | `templates/properties/detail.html` | Galerie + caractéristiques + prix sticky + biens similaires |
| Login / Register | `templates/accounts/login.html`, `register.html` | Formulaire centré, max-width 480px |
| Dashboard client | `templates/transactions/client/dashboard.html` | 4 cartes (visites, dossiers, infos, favoris) |
| Dashboard agent | `templates/transactions/agent/dashboard.html` | 4 KPIs + visites en attente + transactions actives |
| Analytics | `templates/analytics/dashboard.html` | KPIs + graphiques Chart.js + top villes |

---

## 7. Contraintes non fonctionnelles

| Catégorie | Exigence |
|-----------|----------|
| **Responsive** | Mobile (320px) → desktop. Breakpoints Tailwind : `sm/md/lg/xl`. |
| **Accessibilité** | WCAG 2.1 AA : skip-link, focus visible, labels associés, ARIA, contrastes. |
| **Performance** | Lazy loading images, `select_related`/`prefetch_related` sur tous les querysets de listes. |
| **Sécurité** | CSRF, sessions HttpOnly, SameSite Lax, mot de passe min 10 chars, rate-limit login (extension à prévoir). |
| **i18n** | FR par défaut, infrastructure prête pour ajout de langues. |
| **Données** | RGPD : droit d'accès / suppression via `dpo@ymmo.fr`, cookies techniques uniquement. |
