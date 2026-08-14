# Déploiement

## État actuel de l'infrastructure

Docker Compose (développement uniquement — `infra/docker-compose.yml`) :

| Service | Image / build | Notes |
|---|---|---|
| `db` | postgres:16-alpine | volume `pgdata`, healthcheck `pg_isready`, port hôte **5436** |
| `redis` | redis:7-alpine | pas de mot de passe, pas de healthcheck |
| `backend` | `../backend` (dev) | `runserver`, volume code, dépend de `db` healthy |
| `celery_worker` | `../backend` (dev) | `celery -A config worker`, dépend de backend+redis |
| `frontend` | `../frontend` target **dev** | Vite dev server, volume + `node_modules` anonyme |

Un fichier Nginx (`infra/nginx/default.conf`) existe pour la prod (SPA +
proxy `/api/`) mais **n'est rattaché à aucun service** du compose.

### Points de vigilance relevés

| # | Problème | Impact |
|---|---|---|
| 1 | `infra/.env.example` supprimé du dépôt, alors que le README le référence | Setup cassé pour un nouvel arrivant |
| 2 | Dockerfile frontend — stage `production` : `COPY infra/nginx/default.conf` hors du contexte de build (`../frontend`) | **Le build prod échouerait** |
| 3 | Dockerfile backend installe toujours `requirements/dev.txt` (aucun stage prod) | Empreinte/surface d'attaque inutiles en prod |
| 4 | Aucun service Nginx dans le compose, aucun profil `prod` | Pas de chemin de déploiement prod prêt |
| 5 | Redis sans mot de passe ni healthcheck | Serveur prod non durci |
| 6 | `SECRET_KEY` par défaut et `ALLOWED_HOSTS` large en dev | À surcharger strictement en prod |
| 7 | Pas de `restart`, pas de limites de ressources | Résilience faible |

## Checklist de passage en production

### Critique (bloquant)

- [ ] **Secrets** : générer un vrai `DJANGO_SECRET_KEY`, supprimer tout défaut.
- [ ] **HTTPS** : terminaison TLS (Nginx + Let's Encrypt / reverse proxy hébergé),
      ou proxy hébergeur. `SECURE_SSL_REDIRECT` est déjà actif en `prod.py`.
- [ ] **Restaurer `infra/.env.example`** avec des valeurs fictives et le tenir
      à jour (le fichier réel `.env` reste ignoré par git).
- [ ] **Corriger le Dockerfile frontend** (stage production) : copier
      `infra/nginx/default.conf` depuis un contexte élargi ou dupliquer la conf.
- [ ] **Corriger le Dockerfile backend** : multi-stage `dev` / `prod`
      (deps de prod uniquement, gunicorn).
- [ ] **Compose production** : profil `prod` avec Nginx en frontal, `restart:
      unless-stopped`, healthchecks Redis/backend, volumes nommés, ressources.
- [ ] **Mot de passe Redis** (et utilisateur) en prod ; réseaux internes isolés.
- [ ] **Emails transactionnels** : renseigner `EMAIL_HOST`/`EMAIL_PORT`/
      `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` dans l'environnement de prod
      (le backend SMTP est codé dans `prod.py`, mais aucune variable n'est
      fournie par le `.env` actuel). Fournisseur recommandé pour le Maroc :
      SendGrid/Mailgun/SES (délivrabilité) ou Postmark.

### Fortement recommandé

- [ ] **Sauvegardes automatisées** : pg_dump quotidien + retention (offsite,
      testées par restauration).
- [ ] **Monitoring & alerting** : Sentry (exceptions), healthchecks
      `/health/`, métriques système, alertes (UptimeRobot/StatusCake ou équiv.).
- [ ] **Logs centralisés** (Docker + fichiers JSON, Loki/ELK ou hébergeur).
- [ ] **Migrations gérées** : `migrate` comme étape dédiée du déploiement
      (jamais à l'intérieur du conteneur applicatif au démarrage de prod).
- [ ] **Static/media** : `collectstatic` en image (ou CDN) ; `MEDIA_ROOT`
      local vers un stockage objet durable (S3/MinIO/Ceph) — les logos
      coopératives sont persistés localement aujourd'hui.
- [ ] **CORS/ALLOWED_HOSTS stricts** en prod (`CORS_ALLOWED_ORIGINS` = domaine
      frontend exact).
- [ ] **Rate limiting global renforcé** + protection des endpoints publics
      (login, registration, accept-invitation) derrière le WAF du fournisseur.
- [ ] **CI/CD** : ajouter un job de déploiement (pipeline d'images, ou
      git-based deploy) sur `main`. Aujourd'hui la CI s'arrête aux tests.

### Nettoyage / dette technique

- [ ] Documenter le vrai chemin de déploiement (ce fichier) et lier le README.
- [ ] Supprimer l'incohérence de port Postgres (5436 hôte) si elle n'est pas
      intentionnelle, ou documenter.
- [ ] Ajouter un endpoint de santé `/health/` (DB, Redis) utilisé par le
      load balancer / orchestrateur.
- [ ] Centraliser la génération des numéros (un `Sequence`/service commun)
      si des formats doivent devenir configurables par coopérative.
- [ ] Étendre le suivi : la logique de verrouillage de compte
      (`failed_login_attempts`/`locked_until`) est présente mais inactive.

## Stratégie de déploiement recommandée (MVP)

1. **Hébergeur VPS** (Hetzner/OVH/DigitalOcean) ou PaaS (Railway/Fly.io/
   Render — plus rapide pour démarrer).
2. Docker Compose prod en un seul VPS : Nginx (TLS via Caddy ou certbot) +
   backend (gunicorn) + celery + postgres + redis, avec backups cron.
3. Domaine dédié, DNS → VPS, enveloppe `DJANGO_ALLOWED_HOSTS` au domaine.
4. Pipeline CI → push image → deploy SSH ou via CI du PaaS.

Cette architecture couvre un lancement à volume modeste. Pour une montée en
charge, migrer vers un orchestrateur (Kubernetes) ou un PaaS managé plus tard
— l'isolation tenant est déjà entièrement applicative, la base peut rester
partagée.
