# Roadmap des modules à ajouter

Catalogue des **fonctions à ajouter**, organisées en modules — sur le même
principe que les apps backend / features frontend existantes
(`backend/apps/<module>/`, `frontend/src/features/<module>/`).

Légende de priorité :
- **🔴 V1** — Bloquant avant lancement commercial (voir go-to-market.md)
- **🟠 V2** — Différenciation & fidélisation (0–6 mois)
- **🟢 V3** — Conformité & échelle (6–18 mois)

---

## 🔴 Vague 1 — Modules de lancement (monétisation + socle)

### M01 · `subscriptions` — Abonnements & cycle de vie de l'essai
Enforcer le modèle économique (essai 14 jours → plans payants).

Fonctions :
- [ ] Plans tarifaires configurables (basic/pro, cycle mensuel/annuel) — modèle `Plan`, `Subscription`
- [ ] **Enforcement de l'essai** : bascule `trial → suspended` à expiration (tâche planifiée + check middleware)
- [ ] Verrouillage des endpoints métier quand la coopérative est suspendue/expirée
- [ ] Écran de blocage frontend (paywall) avec CTA d'abonnement
- [ ] Facture d'abonnement de la plateforme au client (réutilise billing/accounting)
- [ ] Endpoints : `GET /api/v1/subscriptions/me/`, `POST /subscribe/`, `POST /cancel/`
- Dépend : M02 (paiement), M03 (email)

### M02 · `payments_online` — Paiement en ligne (PSP)
Encaisser les abonnements et (à terme) les factures clients par carte
(CMI) ou Stripe.

Fonctions :
- [ ] Intégration PSP : **CMI (Moov Africa)** + fallback Stripe
- [ ] Checkout d'abonnement (page de paiement sécurisée)
- [ ] **Liens de paiement** sur les factures clients (envoyé avec la facture PDF)
- [ ] Webhooks de confirmation + mise à jour des `Payment` et du solde de facture
- [ ] Statuts / retries des paiements échoués, logs d'audit
- Endpoints : `POST /api/v1/payments/checkout/`, `POST /webhooks/payments/`
- Dépend : backend durci (secrets), TLS

### M03 · `notifications` — Emails transactionnels & files Celery
Tous les emails du produit passent par un canal unique et fiable.

Fonctions :
- [ ] Fournisseur SMTP (SendGrid/Mailgun/SES/Postmark) + variables d'env en prod
- [ ] Templates email (invitation, reset de mot de passe, bienvenue, facture, relance)
- [ ] Abstraction `send_mail_async` → tâche **Celery** (première vraie tâche asynchrone)
- [ ] File d'attente + retries + logs d'échec
- [ ] Préférences de notifications par coopérative (quels événements)
- Dépend : Celery opérationnel en prod

### M04 · `onboarding` — Accueil & prise en main
Réduire le temps de mise en route et le churn précoce.

Fonctions :
- [ ] Écran de bienvenue après inscription (checklist guidée)
- [ ] **Imports Excel/CSV** : adhérents, partenaires, produits (avec prévalidation et rapport d'erreurs)
- [ ] « Données de démo en 1 clic » depuis l'UI (au lieu de la commande `seed_demo_data`)
- [ ] Premier entrepôt + premier compte PCM proposés automatiquement
- [ ] Lien support affiché dans l'app
- Dépend : M03

### M05 · `legal` — Pages légales & conformité
- [ ] CGU, politique de confidentialité (RGPD + loi marocaine 09-08 / CNDP), mentions légales (hébergement, éditeur)
- [ ] Bandeau consentement cookies
- [ ] Modalités de facturation d'abonnement (résiliation, remboursement)
- Dépend : rien (contenu statique + route)

### M06 · `settings` — Compléter le module Paramètres
- [ ] **Route `/settings` manquante** dans App.tsx (l'entrée sidebar existe déjà)
- [ ] Onglets : identité (déjà partiel via `/cooperatives/me/`), préférences langue, logo
- [ ] Abonnement : voir état essai/plan, date de fin, lien vers checkout
- Dépend : M01

---

## 🟠 Vague 2 — Modules de différenciation métier

### M07 · `quotes` — Devis / devis → commande
Convertir un devis en commande de vente en un clic.
- [ ] `Quote` + lignes, statuts `draft → sent → accepted/rejected/expired`
- [ ] Génération PDF du devis
- [ ] Transformation `quote → sales_order` (réutilise les services vente existants)
- [ ] Numéro `DEV-00001`, expiration paramétrable

### M08 · `returns` — Retours & avoirs
Clôturer la boucle commerciale (retours client / fournisseur).
- [ ] Retour client (`return_customer`) → **avoir** (credit note) qui réduit l'encours ou rembourse
- [ ] Retour fournisseur (`return_supplier`) → avoir fournisseur, réconciliation commande achat
- [ ] Avoirs en comptabilité (écritures inversées auto dans billing services)
- [ ] Statut et numéros `AVOIR-00001` ; aucun PATCH/DELETE (immuable)

### M09 · `collections` — Collecte des produits des membres
**Le cœur métier des coopératives agricoles/artisanales** (ex. argan) :
la coop collecte la production des adhérents et la paie.

Fonctions :
- [ ] `Collection` : membre, produit, quantité, qualité/prix unitaire, entrepôt de réception
- [ ] Entrée de stock auto (`reason=initial`/`collection`) + fiche de collecte
- [ ] Valorisation : prix par qualité, total dû au membre
- [ ] Règlement du membre (campagne de paiement, mode caisse/virement)
- [ ] Suivi par campagne (`saison`), rapports par membre et par produit
- Dépend : M01 (RBAC déjà en place), stock existant

### M10 · `cotisations` — Parts sociales & cotisations des membres
- [ ] Souscription/versement de parts (`shares_count` existe déjà sur Member)
- [ ] Échéancier des cotisations, encaissements, soldes par membre
- [ ] Avoir de parts à départ ; écritures comptables (capital social, comptes 101/40)
- [ ] Rapports : capital social total, régularité des cotisants

### M11 · `member_portal` — Portail adhérent (accès séparé)
Levier d'adoption majeur : l'adhérent suit ses comptes sans intervention
du staff.
- [ ] Compte adhérent (login délégué) : relevé de parts, collectes, paiements reçus
- [ ] Voir ses dernières opérations (lecture seule)
- [ ] Télécharger son relevé PDF
- Dépend : M09/M10

### M12 · `reminders` — Relances automatiques
- [ ] Moteur de relances : factures impayées (J+7/J+15/J+30), commandes en retard, stock bas, trial expirant
- [ ] Règles paramétrables par coopérative (délais, canal email/WhatsApp)
- [ ] Journal des relances envoyées (audit)

### M13 · `messaging` — Notifications WhatsApp/SMS
- [ ] Fournisseur SMS (Twilio/Infobip/Nexmo ou passerelle marocaine) + WhatsApp Business API
- [ ] Templates FR/AR, statuts de livraison
- [ ] Envoi depuis l'UI (ex. annonce à tous les adhérents) + déclencheurs métier
- Dépend : M03 (même file d'envoi)

### M14 · `taxes` — TVA & fiscalité de la facture
- [ ] Taux de TVA **paramétrables** par produit/catégorie (20 % en dur aujourd'hui dans le PDF)
- [ ] Mentions légales TVA (IF, patente, CNSS) sur les documents
- [ ] Calcul TVA/total HT-TTC sur factures et devis
- [ ] (V3) exports de déclaration — voir M20

### M15 · `units_conversion` — Conversions & conditionnements
- [ ] Conversions inter-unités (kg↔t, L↔cl, pièce↔carton) par produit
- [ ] Conditionnements (unité de vente vs unité d'achat), prix par conditionnement
- [ ] Affichage multi-unités sur les documents de vente/achat

### M16 · `documents` — Modèles & bons
- [x] Bon de livraison, bon de réception, bon de commande (PDF), réutilise le moteur reporting
- [x] **Modèles personnalisables** par coopérative (logo, couleurs, en-tête/pied)
- [x] Archivage des documents générés (liés aux factures/commandes)

### M17 · `security` — Renforcement
- [ ] **2FA (TOTP)** à l'activation
- [ ] Verrouillage de compte après N échecs (champs `failed_login_attempts`/`locked_until` déjà en base)
- [ ] Journal des sessions/connexions visible côté admin (`audit`)
- [ ] Politique de mot de passe par coopérative (optionnel)

### M18 · `currencies` — Multi-devises
- [ ] Devise de référence (MAD) + devises de facturation (€/$)
- [ ] Taux de change par période, conversion sur les documents et la compta
- [ ] Écritures en devise + équivalent MAD

---

## 🟢 Vague 3 — Modules de conformité & échelle

### M19 · `costing` — Coût de revient & valorisation des stocks
- [ ] Méthodes : **moyenne pondérée**, puis **FIFO** par lot
- [ ] Valorisation des sorties et du stock final sur les rapports
- [ ] Marge par produit / par commande (réutilise les prix de référence)

### M20 · `fiscal` — Déclarations & exports comptables
- [ ] Déclaration TVA pré-remplie (cahier des charges DGI)
- [ ] **Fichier des Écritures Comptables (FEC)**
- [ ] Liasse fiscale / bilan exportable
- [ ] Gestion de l'IF (impôt forfaitaire), patente, CNSS

### M21 · `einvoicing` — Facturation électronique marocaine
- [ ] Veille réglementaire DGI (statuts de conformité évolutifs)
- [ ] Génération des factures électroniques + cachet électronique
- [ ] Archivage légal / export

### M22 · `public_api` — API publique & intégrations
- [ ] Clés API par coopérative (scope/expiration/révocation)
- [ ] Webhooks sortants (événements factures, paiements, stock)
- [ ] Doc OpenAPI publique de ces endpoints

### M23 · `advanced_warehouses` — Entrepôts avancés
- [ ] Emplacements / racks et gestion par lot + dates de péremption
- [ ] Inventaires physiques (comptage, ajustement par écart)
- [ ] Transferts planifiés / multi-périodes

### M24 · `multilang` — Anglais et autres langues
- [ ] Ajout `en` aux locales i18n (backend `SUPPORTED_LANGUAGES`)
- [ ] Généralisation des champs `TranslatedField` déjà présents
- [ ] Bascule langue par utilisateur et par coopérative

### M25 · `analytics` — Pilotage & rapports avancés
- [ ] Rapports personnalisables (colonnes, filtres, périodes)
- [ ] Graphiques (Recharts déjà installé), exports PDF/Excel étendus
- [ ] KPI par adhérent, par produit, par saison (croisements collectes/ventes)

---

## Synthèse et dépendances

```
V1 ─ M02 paiements ──┬─ M01 abonnements ── M05 legal
                     └─ (liens de facture)
     M03 emails ──┬─ M04 onboarding ── M06 settings
                  └─ M12 relances (V2)

V2 ─ M07 devis · M08 avoirs · M09 collectes · M10 cotisations
     M11 portail adhérent · M12 relances · M13 SMS/WhatsApp
     M14 TVA · M15 conversions · M16 documents · M17 sécurité · M18 devises

V3 ─ M19 costing · M20 fiscal · M21 e-facture · M22 API
     M23 entrepôts avancés · M24 multilang · M25 analytics
```

### Ordre de priorité recommandé

1. **M03** (emails) + **M02** (paiement) → débloquent la monétisation.
2. **M01** (abonnement/essai) + **M06** (settings) → premier cycle de vente.
3. **M09** (collectes) et **M10** (cotisations) : cœur de valeur coopératif.
4. **M07/M08** (devis/avoirs) : boucle commerciale complète.
5. **M11** (portail adhérent) : engagement.

Chaque module suit les conventions existantes : app backend `TenantBaseModel`,
RBAC (`<module>.view`/`<module>.edit`), numéros séquentiels atomiques, audit,
i18n FR/AR, frontend feature + sidebar filtré.
