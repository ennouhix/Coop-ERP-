# Go-to-market — Évolutions nécessaires au lancement

Ce document évalue la maturité actuelle du produit et liste, par ordre de
priorité, les évolutions à réaliser avant et après le lancement commercial.

## 1. État des lieux produit

### ✅ Prêt / solide

- Socle SaaS multi-tenant **testé** (isolation garantie par test d'introspection).
- Authentification complète : JWT, throttle anti brute-force, reset de mot de
  passe, blacklist, changement de mot de passe.
- Cycle métier complet et **cohérent** : adhérents → catalogue → stock →
  achats → ventes → facturation → comptabilité PCM → audit.
- Intégrité forte : numéros séquentiels atomiques, immuabilité des ledgers,
  transactions couplées, équilibre comptable obligatoire.
- RBAC par rôle avec surcharges par coopérative, appliqué côté API **et**
  sidebar.
- Bilinguisme FR/AR avec RTL, rapports PDF/Excel, données de démo.
- CI verte (ruff, mypy, pytest ≥ 80 %, eslint, tsc, vitest) sur les PR.

### ❌ Non prêt pour le lancement

| Domaine | Constat | Conséquence |
|---|---|---|
| **Déploiement prod** | Pas de chemin de déploiement : Dockerfile frontend prod cassé, backend toujours en dev deps, pas de service Nginx dans le compose, pas de CI/CD de déploiement | Impossible de mettre en ligne tel quel |
| **Monétisation** | `subscription_plan`/`status`/`trial_ends_at` existent mais **rien ne bloque** une coopérative en fin d'essai ou suspendue ; aucun système de paiement ni de souscription | Pas de revenus |
| **Emails** | SMTP codé dans `prod.py` mais aucune variable d'email dans `.env` ; reset/invitation fonctionnent en console en dev | Invitations et reset inopérants en prod |
| **Paiement en ligne** | `Payment` = encaissement **saisi manuellement** (caisse/virement/chèque/CMI) ; aucun PSP | Pas de paiement client en ligne |
| **Trial & onboarding** | Aucune mécanique de fin d'essai, aucun processus d'accueil (demo, templates, support) | Churn précoce |
| **Légal / conformité** | Pas de CGU, politique de confidentialité, mentions légales, ni de gestion RGPD/CNIL-Maroc (CNDP) | Bloquant pour un SaaS public |
| **Observabilité** | Pas de Sentry/monitoring/alertes, pas d'endpoint `/health/` | Ops aveugle |
| **Sauvegardes** | Aucune stratégie de backup | Perte de données possible |

## 2. Vague 1 — Bloquants avant lancement (priorité maximale)

Objectif : pouvoir vendre à un premier client sans risque.

### 2.1 Infrastructure & déploiement
- Restaurer `infra/.env.example` et le maintenir à jour.
- Corriger le Dockerfile frontend (copie de la conf Nginx dans le contexte de
  build) et rendre le backend multi-stage `dev`/`prod`.
- Compose de production : Nginx frontal + TLS (Let's Encrypt), `restart`,
  healthchecks, Redis sécurisé, volumes.
- Endpoint `/health/` (DB + Redis) pour l'orchestrateur.
- **CI/CD de déploiement** sur `main` (job GitHub Actions ou PaaS).
- Sauvegardes PostgreSQL automatisées (quotidiennes, offsite, restauration testée).
- Monitoring : **Sentry** (backend + frontend) + alertes de disponibilité.
- Envoyer les **emails** (SMTP) : invitations, reset, notification d'abonnement.

### 2.2 Monétisation & cycle de vie de l'abonnement
- Définir les **plans** (basic/pro) et tarifs, puis modéliser la facturation
  des abonnements (cycle mensuel/annuel, statuts).
- **Enforcer l'essai de 14 jours** : middleware/check qui bascule une
  coopérative en `suspended` à expiration, verrouille les endpoints métier et
  affiche un écran de blocage côté frontend.
- **Checkout en ligne** : intégrer un PSP marocain (Stripe/Moov (CMI)) pour le
  paiement de l'abonnement et, à terme, les encaissements clients.
- Portail de facturation des abonnements (facture de la plateforme au client).
- **Onboarding** : écran de bienvenue, imports (Excel adhérents/produits),
  données de démo en un clic, lien support.

### 2.3 Légal & conformité
- Pages **CGU, politique de confidentialité, mentions légales** (éditeur,
  hébergement, RGPD + loi marocaine 09-08 — CNDP), cookies.
- Consentement et suppression de données (droit à l'effacement) côté produit.

### 2.4 Dette frontend à corriger avant le lancement
- Route `/settings` manquante alors que l'entrée existe dans le sidebar.
- **Traductions incomplètes** : comptabilité, dashboard et reporting
  contiennent du français en dur — le bilingue FR/AR est une promesse de
  vente, il doit être complet.
- Ajouter des **tests frontend** (vitest est configuré mais aucun test n'existe).

## 3. Vague 2 — Différenciation & fidélisation (0–6 mois)

Une fois le produit vendable, ces évolutions augmentent la valeur perçue :

- **Notifications** : email (aujourd'hui), puis **WhatsApp/SMS** (très attendu
  par les coopératives marocaines : alertes stock bas, commandes, échéances
  de paiement, anniversaires d'adhésion).
- **Portail adhérent** (web) : consultation de ses parts, collectes, relevés —
  levier majeur d'adoption dans une coopérative.
- **Gestion de la TVA** : taux configurables par produit/catégorie (20 %
  actuellement en dur dans le PDF), mentions légales paramétrables.
- **Paiement en ligne des factures** par le client final (lien de paiement
  CMI/Stripe sur la facture PDF).
- **Relances automatiques** des factures impayées (workflow email).
- **Devises** : comptabilité en MAD (défaut), export multi-devises (€/$) pour
  la vente à l'international.
- **Unités de conversion** et conditionnements (poids/volume), colisage.
- **Personnalisation** : thème/logo (déjà possible), modèles de documents
  (facture, bon de livraison, bon de commande) par coopérative.
- **Sécurité avancée** : 2FA/TOTP, verrouillage de compte
  (`failed_login_attempts` est déjà en base), journal de connexion visible.

## 4. Vague 3 — Conformité & échelle (6–18 mois)

- **Facturation électronique marocaine** : alignement DGI (génération et
  archivage des factures électroniques, cachet électronique) — en veille car la
  réglementation évolue.
- **Déclarations** : export pré-rempli TVA (Cahier des charges DGI), liasse
  fiscale, fichier d'écritures comptables (FEC).
- **Multi-entrepôts avancés**, coût de revient (méthodes FIFO/moyenne pondérée).
- **API publique** (tokens pour intégrations tierces : banques, marketplaces).
- **Robustesse** : migrations en availability mode, caching des listes
  fréquentes, index supplémentaires si le volume grossit, sharding/HA si
  nécessaire.
- **Multi-lingue étendu** : ajout de l'anglais (et éventuellement du tachelhit)
  pour viser d'autres marchés.

## 5. Sujets non fonctionnels (parallèle)

- **Proposition de valeur & site vitrine** : landing FR/AR, démo guidée,
  capture d'email.
- **Pricing** : tester un positionnement (ex. essai 14 j → 200–500 MAD/mois
  pour une coopérative, plans basic/pro).
- **Support** : email + (à terme) chat ; base de connaissances FR/AR.
- **Sales/Branding** : identité, vidéo démo, présence LinkedIn/réseaux
  coopératifs (ODCO, réseaux féminins — les coopératives sont souvent portées
  par des femmes).
- **Financement de l'essai** : outils d'analyse (Plausible/GA4), NPS, suivis
  de conversion.

## 6. Risques & mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Fuite de données inter-tenant | Faible (testée) | Critique | Garder le test d'introspection vert ; revue de tout nouveau modèle ; pen-test avant lancement |
| Vol de tokens / XSS | Moyenne | Élevé | JWT en mémoire (déjà fait), CSP, 2FA en Vague 2 |
| Churn pendant l'essai | Élevée | Moyen | Onboarding guidé, données de démo, notifications, portail adhérent |
| Perte de données | Moyenne | Critique | Backups automatisés + restauration testée, disques volumétriques |
| Concurrence (ERP coopératives) | Moyenne | Moyen | Positionnement vertical (PCM, règles coop, FR/AR), réactivité locale |
| Changement réglementaire (e-facture) | Moyenne | Moyen | Veille DGI, architecture extensible des rapports |

## 7. KPIs de succès (premiers 6 mois)

- Conversion essai → payant ≥ 15 %.
- Churn mensuel ≤ 3 %.
- 1 000 coopératives en essai cumulées (ou cible cohérente avec la force de
  vente), 50+ payantes.
- Temps moyen de prise en main < 1 jour (démo + données).
- Downtime < 99,9 % ; RPO < 24 h (backups) ; RTO < 4 h.
- Satisfaction : NPS ≥ 40, tickets/résolus < 48 h.

## 8. Recommandation immédiate

Prioriser dans cet ordre :

1. **Réparer le chemin de déploiement** (items 2.1) — 1 semaine.
2. **Emails SMTP** — 1 jour (variables + test).
3. **Enforcement essai/abonnement** + écran de blocage — 2–3 jours.
4. **Traductions complètes + route /settings + tests frontend** — 3–5 jours.
5. **Pages légales** — 1–2 jours (contenu statique).
6. **PSP (CMI/Stripe)** pour l'abonnement — 1–2 semaines.

Soit environ **3–4 semaines** d'effort ciblé pour un MVP commercialisable.
