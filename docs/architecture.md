# Architecture technique

## Vue d'ensemble

```
                    ┌────────────────────────────────────────────┐
                    │            Navigateur (React SPA)           │
                    │  Vite dev (5173)  /  Nginx prod (80/443)    │
                    └───────────────┬────────────────────────────┘
                                    │  JSON / HTTPS
                                    ▼
                    ┌────────────────────────────────────────────┐
                    │              Django REST API                │
                    │        TenantAwareJWTAuthentication         │
                    │         TenantMiddleware (reset)            │
                    │              TenantManager                  │
                    └───┬───────────────┬────────────────────┬────┘
                        │               │                    │
                        ▼               ▼                    ▼
                 ┌────────────┐  ┌────────────┐      ┌──────────────┐
                 │ PostgreSQL │  │   Redis    │      │   Celery     │
                 │ (tenant DB)│  │ cache/broker│     │ (worker)     │
                 └────────────┘  └────────────┘      └──────────────┘
```

Le frontend consomme exclusivement l'API REST (`/api/v1/`). L'authentification
est **stateless (JWT)** ; le multi-tenancy est résolu par claim JWT, sans
sous-domaine ni chemin de tenant.

## Multi-tenancy (pièce maîtresse)

### Principe

Chaque coopérative est un tenant isolé. Toute table métier hérite de
`TenantBaseModel` (`apps/core/models.py`) :

- champ `cooperative` (FK `Cooperative`, obligatoire, indexée) ;
- manager par défaut `TenantManager` qui **filtre automatiquement** sur le
  tenant courant : `Product.objects.all()` ne renvoie que les produits de la
  coopérative active — impossible d'oublier le filtre par erreur ;
- manager `all_objects` (non filtré) réservé aux cas précis : activation /
  désactivation d'un enregistrement, scripts admin, migrations, tâches système.

### Résolution du tenant

1. `LoginView` / inscription retournent un JWT dont les claims embarquent
   `cooperative_id` et `role`.
2. `TenantAwareJWTAuthentication` (`apps/core/authentication.py`) est exécuté
   par DRF **au moment de l'authentification**, avant toute vue : il appelle
   `set_current_tenant(user.cooperative_id)`.
3. `TenantManager.get_queryset()` lit ce tenant via `get_current_tenant()`
   (`apps/core/context.py`, implémentation **contextvars** — compatible async).
4. `TenantMiddleware` (`apps/core/middleware.py`) est un filet de sécurité qui
   remet le contexte à `None` au début et à la fin de chaque requête (évite les
   fuites de tenant entre requêtes d'un même worker).

> ⚠️ **Bug critique corrigé (Epic 4)** : un middleware Django classique ne peut
> pas lire `request.user` pour une API JWT (l'utilisateur n'est peuplé qu'à
> l'authentification DRF, plus tard dans le cycle). Sans cette correction, le
> filtre tenant n'était JAMAIS appliqué → fuite de données inter-coopératives.

### Garde-fou automatique

`backend/apps/core/tests/test_tenant_isolation.py` (test d'introspection) :
il vérifie que **tout modèle métier** hérite de `TenantBaseModel`. Ce test
échoue dès qu'un nouveau modèle est ajouté sans isolation — il doit rester
vert en permanence.

## Authentification & sécurité

### JWT (SimpleJWT)

- Access token : **15 min** · Refresh token : **7 jours**.
- `ROTATE_REFRESH_TOKENS=True` + `BLACKLIST_AFTER_ROTATION=True`.
- Claims ajoutés : `cooperative_id`, `role`, `email`.
- Compte désactivé → refus explicite (`account_disabled`).

### Endpoints d'authentification (`/api/v1/auth/`)

| Méthode | Path | Rôle |
|---|---|---|
| POST | `/auth/login/` | Connexion (tokens + profil `user`) |
| POST | `/auth/refresh/` | Renouveler l'access token |
| POST | `/auth/logout/` | Blacklister le refresh token (205) |
| GET/PATCH | `/auth/me/` | Profil / mise à jour (inclut `modules` RBAC) |
| POST | `/auth/password/change/` | Changer son mot de passe (blackliste **tous** les refresh) |
| POST | `/auth/password/reset/` | Email de reset (toujours 200, anti-énumération) |
| POST | `/auth/password/reset/confirm/` | Appliquer le nouveau mot de passe |

### Throttling (anti brute-force)

- Login : **5 tentatives / 15 min par email** (`LoginRateThrottle`, repli IP).
- Password reset : 3 / heure / email+IP.
- Globaux : user `1000/hour`, anon `100/hour`.
- Inscription coopérative : 5 / heure / IP.

> Note : les champs `failed_login_attempts` et `locked_until` existent sur
> `User` mais la logique de verrouillage **n'est pas implémentée** dans le flux
> de login (la protection repose sur le throttle).

### Protection des données

- **UUID** en clé primaire (pas d'énumération d'IDs, sensible en SaaS).
- **Soft delete** (`is_active`, `deleted_at`) — en ERP, on ne supprime jamais
  réellement une donnée liée à des mouvements.
- **JWT en mémoire** côté frontend (jamais en `localStorage`, anti-XSS).
- Format d'erreur unifié : `{"error": {"code", "message", "details"}}`
  (`apps/core/exceptions.py`).
- Validation des mots de passe : longueur ≥ 10, anti-mot-de-passe-commun, etc.

## RBAC — Rôles & Permissions

### Rôles

`owner` (accès total), `admin`, `staff`, `accountant`. Rôles éditables depuis
le panneau d'administration : `admin`, `staff`, `accountant`.

### Matrice statique (défaut)

`apps/roles_permissions/matrix.py` — codes `<module>.<action>`, 13 modules :
`users, cooperative, members, partners, catalog, warehouses, stock, purchases,
sales, billing, reports, audit, accounting`.

- **OWNER** = `"*"` toujours.
- **ADMIN** : tout (y compris comptabilité, audit, gestion d'équipe).
- **ACCOUNTANT** : comptabilité + édition (billing, partenaires), lecture large,
  pas d'opérations de stock/ventes/achats.
- **STAFF** : opérations terrain (membres, stock, achats, ventes), pas de
  comptabilité ni d'audit.

### Surcharges par coopérative

`RoleModuleAccess` (modèle `TenantBaseModel`) : si des lignes existent pour un
couple `(cooperative, role)`, elles **remplacent intégralement** la matrice pour
ce rôle. Endpoint `GET/PUT /api/v1/roles/permissions/` (OWNER/ADMIN).

### Application

- `RequirePermission("code")` — factory DRF qui vérifie via
  `has_permission_for_cooperative()` (OWNER → true, sinon surcharges puis
  matrice). La vérification se fait **au niveau module**.
- `IsCooperativeMember`, `IsOwnerOrAdmin` (cooperatives, users).

### Côté frontend

Le profil user (`/login`, `/me`) expose `modules` (modules effectifs du rôle).
Le **sidebar est filtré dynamiquement** (`navConfig.tsx` associe chaque entrée
à un module RBAC ; `Sidebar.tsx` n'affiche que les entrées autorisées).
C'est un masquage UI — l'autorité reste le backend.

## Patterns transverses

### Numérotation séquentielle atomique

Toutes les références sont générées avec un verrou pessimiste
(`select_for_update` sur la ligne `Cooperative`) pour garantir l'unicité sous
concurrence :

| Entité | Format | Exemple |
|---|---|---|
| Membre | `<SLUG3>-NNNN` | `ARG-0001` |
| Partenaire | `PART-NNNN` | `PART-0001` |
| Produit (SKU) | `PRD-NNNNN` | `PRD-00001` |
| Entrepôt | `WH-NNNN` | `WH-0001` |
| Commande achat | `PO-NNNNN` | `PO-00001` |
| Commande vente | `SO-NNNNN` | `SO-00001` |
| Facture | `FAC-NNNNN` | `FAC-00001` |
| Écriture comptable | `<JOURNAL>-YYYY-NNNNN` | `JV-2026-00001` |

Les numéros sont **immuables** après création.

### Immuabilité (INSERT only)

`StockMovement` (ledger de stock), `Payment` (encaissements) et `AuditLog`
(journal d'audit) sont **append-only** : aucune route PATCH/DELETE n'existe —
l'historique ne peut pas être falsifié.

### Transactions couplées

- Réception d'achat ⇄ entrée de stock (même transaction).
- Livraison de vente ⇄ sortie de stock + contrôle de stock suffisant.
- Paiement ⇄ mise à jour du solde de facture (facture verrouillée).
- Écriture comptable ⇄ équilibre débit/crédit obligatoire.
- Émission/encaissement de facture ⇄ écritures comptables automatiques.

### Bilinguisme FR/AR

Champs traduits via `TranslatedField` (JSON `{"fr": ..., "ar": ...}`) côté
backend (noms de produits, catégories, comptes, etc.). Côté frontend :
i18next + fichiers `locales/{fr,ar}/common.json`, bascule **RTL** pour l'arabe.

### Frontend — structure & état

- **Organisation par feature** : `frontend/src/features/<module>/` miroir des
  apps backend, partage via `frontend/src/shared/` (layout, UI, i18n, routing).
- **État global** : Zustand (`authStore`) — user + tokens en mémoire.
- **Client API** : Axios central (`api/client.ts`) — injection du token,
  renouvellement automatique du refresh (rotation), normalisation des erreurs.
- **TypeScript strict** : `noUnusedLocals`, `noUnusedParameters`, etc.
- **Tailwind RTL-safe** : classes logiques uniquement (`ms-`, `me-`, `ps-`,
  `pe-`, `text-start/end`) — jamais `ml-`, `text-left`, etc.
