# Coop ERP — SaaS pour coopératives marocaines

ERP SaaS multi-tenant, bilingue FR/AR, construit avec Django REST Framework + React/TypeScript.

## Stack

- **Backend** : Python 3.12, Django 5.1, DRF, PostgreSQL 16, Redis, Celery, JWT
- **Frontend** : React 18, TypeScript, Vite, Tailwind CSS, i18next (FR/AR + RTL)
- **Infra** : Docker, Docker Compose, Nginx, GitHub Actions

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
- `db` — PostgreSQL sur le port 5432
- `redis` — Redis sur le port 6379
- `backend` — API Django sur http://localhost:8000
- `celery_worker` — worker de tâches asynchrones
- `frontend` — React/Vite sur http://localhost:5173

### 4. Initialiser la base de données

Dans un nouveau terminal :

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
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

Voir `docs/architecture/` pour le détail de l'architecture multi-tenant,
la stratégie d'isolation des données, et les conventions de code.

Chaque app Django dans `backend/apps/` correspond à un module métier
(voir la Roadmap du projet). Le frontend suit la même organisation dans
`frontend/src/features/`.

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

