# Coop ERP — SaaS pour coopératives marocaines

ERP SaaS multi-tenant, bilingue FR/AR, construit avec Django REST Framework + React/TypeScript.

## Stack

- **Backend** : Python 3.12, Django 5.1, DRF, PostgreSQL 16, Redis, Celery, JWT
- **Frontend** : React 18, TypeScript, Vite, Tailwind CSS, i18next (FR/AR + RTL)
- **Infra** : Docker, Docker Compose, Nginx, GitHub Actions

## Documentation

La documentation complète se trouve dans [`docs/`](docs/README.md) :

- [Architecture & multi-tenancy](docs/architecture.md)
- [Modules métier & API](docs/modules.md)
- [Développement & conventions](docs/development.md)
- [Déploiement](docs/deployment.md)
- [Go-to-market & évolutions](docs/go-to-market.md)

## Démarrage rapide (développement local)

### 1. Prérequis
- Docker & Docker Compose installés
- Git

### 2. Cloner et configurer

```bash
cp infra/.env.example infra/.env
# éditer infra/.env si besoin (mots de passe, secrets)
```

### 3. Lancer les services

```bash
cd infra
docker compose up --build
```

Cela démarre :
- `db` — PostgreSQL sur localhost:5436 (→ 5432 dans le conteneur)
- `redis` — Redis sur le port 6379
- `backend` — API Django sur http://localhost:8000
- `celery_worker` — worker de tâches asynchrones
- `frontend` — React/Vite sur http://localhost:5173

### 4. Initialiser la base de données

Dans un nouveau terminal :

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
# (optionnel) données de démo avec cycle métier complet :
docker compose exec backend python manage.py seed_demo_data
```

### 5. Accéder à l'application

- Frontend : http://localhost:5173
- API : http://localhost:8000/api/
- Documentation API (Swagger) : http://localhost:8000/api/docs/
- Admin Django : http://localhost:8000/admin/

## Lancer les tests

```bash
docker compose exec backend pytest --cov=apps
```

Le test `apps/core/tests/test_tenant_isolation.py` est un **garde-fou critique** :
il échoue automatiquement si un nouveau modèle métier est ajouté sans hériter
de `TenantBaseModel`, ce qui empêche toute fuite de données entre coopératives.

## Structure du projet

```
backend/
  apps/            # modules métier Django (auth, members, catalog, stock, ...)
  config/          # settings (base/dev/prod/test), urls, wsgi/asgi, celery
frontend/
  src/features/    # mêmes modules côté React (feature folders)
  src/shared/      # layout, UI, i18n, routing, api
infra/             # docker-compose, nginx, .env
.github/workflows/ # CI backend (ruff/mypy/pytest) et frontend (eslint/tsc/vitest)
docs/              # documentation du projet
```

## Conventions

- Backend : PEP8, type hints obligatoires, docstrings, `ruff` + `mypy` en CI
- Frontend : TypeScript strict, classes Tailwind **logiques** uniquement
  (`ms-`, `me-`, `ps-`, `pe-`, `text-start`, `text-end`) pour garantir le
  support RTL de l'arabe — jamais `ml-`, `mr-`, `pl-`, `pr-`, `text-left/right`
- Toute table métier hérite de `TenantBaseModel` (isolation multi-tenant)
- Couverture de tests minimale : 80 % (backend)

## Statut du projet

- [x] Epic 0 — Architecture & Infrastructure (squelette actuel)
- [x] Epic 1 — Authentification & Sécurité
- [x] Epic 2 — Gestion des coopératives
- [x] Epic 3 — Utilisateurs, Rôles, Permissions
- [x] Epics 4+ — Modules métier (membres, partenaires, catalogue, entrepôts,
      stock, achats, ventes, facturation, tableau de bord, reporting, audit,
      comptabilité PCM)

Le socle fonctionnel est en place et testé ; le passage en production et le
lancement commercial nécessitent encore des évolutions — voir
[docs/go-to-market.md](docs/go-to-market.md).
