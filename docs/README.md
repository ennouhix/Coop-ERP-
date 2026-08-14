# Documentation — Coop ERP

ERP SaaS multi-tenant destiné aux **coopératives marocaines**, bilingue
**FR / AR** (avec support RTL), couvrant l'ensemble du cycle de vie d'une
coopérative : adhérents, partenaires, catalogue, stock, achats, ventes,
facturation, comptabilité (PCM marocain), reporting et audit.

## Sommaire de la documentation

| Document | Contenu |
|---|---|
| [Architecture](architecture.md) | Conception multi-tenant, sécurité, RBAC, patterns transverses, stack frontend |
| [Modules métier & API](modules.md) | Fonctionnalités, modèles, endpoints et règles de chaque module |
| [Développement](development.md) | Setup local, commandes utiles, tests, conventions de code |
| [Déploiement](deployment.md) | Environnements, Docker, variables, checklist production |
| [Go-to-market](go-to-market.md) | Évolutions nécessaires avant et après le lancement commercial |
| [Roadmap modules](roadmap-modules.md) | Catalogue des fonctions à ajouter, par module (V1/V2/V3) |

## Vue d'ensemble

Coop ERP est une application **SaaS** : chaque coopérative est un *tenant*
isolé qui ne voit jamais les données des autres. L'inscription est
self-service (création de la coopérative + compte OWNER), suivie d'un
**essai gratuit de 14 jours** avant passage à un plan payant (`basic`/`pro`).

Le produit est organisé en **17 apps Django** (`backend/apps/`) reflétées
côté frontend par des *features* (`frontend/src/features/`) :

- **Données de base** : members, partners, catalog, warehouses
- **Opérations** : inventory, purchases, sales, billing
- **Gouvernance & support** : cooperatives, users, roles_permissions, audit
- **Décision** : dashboard, reporting, accounting
- **Socle** : core, authentication

## Stack technique

| Couche | Technologies |
|---|---|
| Backend | Python 3.12, Django 5.1, Django REST Framework, SimpleJWT, django-filter |
| Base de données | PostgreSQL 16 (multi-tenant, isolation par `cooperative_id`) |
| Cache / files d'attente | Redis 7, Celery 5 (broker configuré, pas encore de tâches) |
| Frontend | React 18, TypeScript 5.7 (strict), Vite 6, Tailwind CSS 3, i18next (FR/AR + RTL), Zustand, Recharts, Axios |
| Rapports | ReportLab (PDF), OpenPyXL (Excel) |
| Infrastructure | Docker, Docker Compose, Nginx, GitHub Actions |
| Qualité | Ruff, mypy (django-stubs), ESLint, pytest (couverture ≥ 80 %) |

## Statut du projet

| Epic | Contenu | Statut |
|---|---|---|
| Epic 0 | Architecture & infrastructure multi-tenant | ✅ Livré |
| Epic 1 | Authentification & sécurité (JWT, throttle, reset) | ✅ Livré |
| Epic 2 | Gestion des coopératives (inscription, essai 14 j) | ✅ Livré |
| Epic 3 | Utilisateurs, rôles, permissions (RBAC) | ✅ Livré |
| Epic 4+ | Modules métier : membres, partenaires, catalogue, entrepôts, stock, achats, ventes, facturation, tableau de bord, reporting, audit, comptabilité | ✅ Livré |

Le socle fonctionnel est **en place et testé** (~210 tests backend).
Le passage en production et le lancement commercial nécessitent encore
plusieurs évolutions — voir [go-to-market.md](go-to-market.md).

## Démarrage rapide

```bash
cp infra/.env.example infra/.env   # créer le fichier si absent
cd infra
docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo_data
```

- Frontend : http://localhost:5173
- API : http://localhost:8000/api/
- Swagger : http://localhost:8000/api/docs/
- Admin Django : http://localhost:8000/admin/

Détails dans [development.md](development.md).

## Liens utiles

- API publique : registre des coopératives, acceptation d'invitation, login
- `seed_demo_data` : coopérative de démo avec cycle métier complet
- `load_pcm` : plan comptable marocain + journaux
- Test `test_tenant_isolation` : garde-fou d'isolation multi-tenant
