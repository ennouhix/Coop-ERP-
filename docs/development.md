# Développement

## Prérequis

- Docker & Docker Compose
- Git

## Setup local (Docker)

```bash
# 1. Fichier d'environnement (créer depuis le modèle si absent)
cp infra/.env.example infra/.env

# 2. Lancer les services
cd infra
docker compose up --build

# 3. Appliquer les migrations
docker compose exec backend python manage.py migrate

# 4. (Optionnel) Données de démo
docker compose exec backend python manage.py seed_demo_data
```

Services démarrés :

| Service | Adresse |
|---|---|
| Frontend (Vite) | http://localhost:5173 |
| API Django | http://localhost:8000/api/ |
| Swagger | http://localhost:8000/api/docs/ |
| Admin Django | http://localhost:8000/admin/ |
| PostgreSQL | localhost:5436 (hôte) → 5432 (conteneur) |
| Redis | localhost:6379 |

### Sans Docker (recommandé pour le développement rapide)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
# PostgreSQL local + Redis requis ; configurer les variables DB_* 
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py runserver
```

## Variables d'environnement

Lues via python-decouple (`config/settings/base.py`), à définir dans `infra/.env` :

| Variable | Défaut (dev) | Usage |
|---|---|---|
| `DJANGO_SECRET_KEY` | `unsafe-dev-key-change-me` | Signature JWT, sessions |
| `DJANGO_DEBUG` | `False` | Mode debug |
| `DJANGO_SETTINGS_MODULE` | — | `config.settings.dev` en dev |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hôtes autorisés |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | `coop_erp` / `coop_erp` / `devpassword` | PostgreSQL |
| `DB_HOST` / `DB_PORT` | `localhost` / `5432` | PostgreSQL |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery / cache |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Origines frontend |
| `FRONTEND_URL` | `http://localhost:5173` | Liens dans les emails |

Configurations Django : `config/settings/{base,dev,prod,test}.py`.

## Tests

### Backend (pytest)

```bash
docker compose exec backend pytest --cov=apps
# ou
cd backend && pytest --cov=apps --cov-report=term-missing --cov-fail-under=80
```

- ~210 tests sur 20 fichiers, couverture minimale exigée : **80 %** (en CI).
- Le test `apps/core/tests/test_tenant_isolation.py` est un **garde-fou
  critique** : il échoue si un modèle métier est ajouté sans hériter de
  `TenantBaseModel`.
- `config/settings/test.py` : hashing MD5 (rapide), Celery en mode EAGER.
- Les tests utilisent `APITestCase`/`TestCase` (sauf accounting : fixtures).

### Frontend (vitest)

```bash
cd frontend && npm run test
```

⚠️ Aucun test frontend n'existe encore malgré vitest configuré (script `test`
prêt à l'emploi).

## Qualité & lint

| Outil | Commande | Config |
|---|---|---|
| ruff (backend) | `ruff check .` | `backend/pyproject.toml` (E/F/I/UP/B/DJ, line-length 100) |
| mypy (backend) | `mypy apps` | django-stubs |
| ESLint (frontend) | `npm run lint` | `frontend/` |
| tsc (frontend) | `npm run build` (tsc -b + vite) | `frontend/tsconfig.json` (strict) |

## Conventions de code

### Backend

- Type hints **obligatoires**, docstrings françaises, PEP8.
- Toute table métier hérite de `TenantBaseModel` (isolation tenant).
- Écrire des tests pour toute nouvelle règle métier (couverture ≥ 80 %).
- Ne jamais modifier un numéro de référence après création (immuable).
- Utiliser `all_objects` (manager non filtré) uniquement quand nécessaire.

### Frontend

- TypeScript strict ; classes Tailwind **logiques** uniquement pour le RTL :
  `ms-`, `me-`, `ps-`, `pe-`, `text-start`, `text-end` — **jamais** `ml-`,
  `mr-`, `pl-`, `pr-`, `text-left`, `text-right`.
- Tout libellé UI passe par i18n (`locales/fr/common.json` + `ar/`), en FR
  comme en AR.
- Organisation par feature : `src/features/<module>/`, partage dans `src/shared/`.

## Workflow Git & CI

- Branches : `main` (stable) et `develop` ; PR ciblant l'une des deux.
- CI GitHub Actions :
  - `backend-ci.yml` : ruff + mypy + pytest (PostgreSQL 16 en service, seuil 80 %).
  - `frontend-ci.yml` : eslint + tsc/build + vitest.
- Déclenchée sur les PR et les push touchant `backend/**` / `frontend/**`.

## Debug & outils

- Swagger interactif : http://localhost:8000/api/docs/
- Schéma OpenAPI : `GET /api/schema/`
- Admin Django : http://localhost:8000/admin/ (créer via `createsuperuser`)
- Logs : `docker compose logs -f backend`
- Redis CLI : `docker compose exec redis redis-cli`
