# Modules métier & API

Toutes les routes sont montées sous `/api/v1/`. Les permissions reposent sur
le RBAC (voir [architecture.md](architecture.md)). Les erreurs sont uniformisées
au format `{"error": {"code", "message", "details"}}`.

## Vue d'ensemble

| Module | Route | Modèles principaux | Immuable ? |
|---|---|---|---|
| Authentification | `/auth/` | `User` | — |
| Coopératives | `/cooperatives/` | `Cooperative` (tenant racine) | — |
| Équipe | `/users/` | `Invitation` | — |
| Rôles & permissions | `/roles/permissions/` | `RoleModuleAccess` | — |
| Membres | `/members/` | `Member` | — |
| Partenaires | `/partners/` | `Partner` | — |
| Catalogue | `/catalog/` | `Unit`, `Category`, `Product` | — |
| Entrepôts | `/warehouses/` | `Warehouse` | — |
| Stock | `/inventory/` | `StockLevel`, `StockMovement` | `StockMovement` |
| Achats | `/purchases/` | `PurchaseOrder(+Line)` | — |
| Ventes | `/sales/` | `SalesOrder(+Line)` | — |
| Facturation | `/billing/` | `Invoice(+Line)`, `Payment` | `Payment` |
| Tableau de bord | `/dashboard/` | — (agrégats) | — |
| Reporting | `/reporting/` | — (PDF/Excel) | — |
| Audit | `/audit/` | `AuditLog` | `AuditLog` |
| Comptabilité | `/accounting/` | `Account`, `Journal`, `AccountingEntry(+Line)` | — |

## Workflows de statuts

```
Achat   : draft → confirmed → partially_received → received
                              └──> received
          cancelled (draft/confirmed, aucune réception)

Vente   : draft → confirmed → partially_delivered → delivered
                              └──> delivered
          cancelled (draft/confirmed, aucune livraison)

Facture : draft → issued → partially_paid → paid
          cancelled (draft/issued, aucun paiement)

Invitation : pending → accepted | cancelled

Abonnement : trial → active | suspended | cancelled
```

---

## 1. Membres — `/members/`

Adhérents/producteurs de la coopérative (≠ utilisateurs employés).

- `Member` : `member_number` (auto `ARG-0001`), `member_type`
  (`individual`/`entity`), identité, CIN (`^[A-Za-z]{1,2}\d{1,6}$`), téléphone,
  `join_date`, `status` (`active`/`suspended`/`inactive`), `shares_count`.
  Numéro et CIN uniques par coopérative.
- Endpoints : `GET/POST /members/`, `GET/PATCH /members/{id}/`,
  `POST /members/{id}/deactivate/`, `POST /members/{id}/reactivate/`.
- Recherche : numéro, nom, téléphone, CIN. Filtres : `status`, `member_type`,
  `join_date_after/before`.

## 2. Partenaires — `/partners/`

Tiers commerciaux uniques (un partenaire peut être client **et/ou** fournisseur).

- `Partner` : `code` (auto `PART-0001`), `is_customer`, `is_supplier`
  (au moins un des deux), `ice` (15 chiffres), `payment_terms_days`
  (échéance factures), `credit_limit` (encours max), `status`.
- Endpoints : `GET/POST /partners/`, `GET/PATCH /partners/{id}/`,
  `POST /partners/{id}/deactivate/`, `POST /partners/{id}/reactivate/`.

## 3. Catalogue — `/catalog/`

- `Unit` : unité de mesure (type `weight`/`volume`/`count`/`length`).
- `Category` : hiérarchique (anti-cycles dans `clean()`), noms bilingues.
- `Product` : `sku` (auto `PRD-00001`), `barcode`, nom bilingue, `category`,
  `unit` (FK PROTECT), prix d'achat/vente de référence, `minimum_stock_threshold`
  (alerte stock bas), `is_sellable`, `is_purchasable`.
- Endpoints : `/catalog/units/`, `/catalog/categories/`,
  `/catalog/products/` (+ `{id}/`, `deactivate/`, `reactivate/`).
- Recherche : `sku`, `barcode`. Filtres : `category`, `unit`, flags.

## 4. Entrepôts — `/warehouses/`

- `Warehouse` : `code` (auto `WH-0001`), `manager`, `is_default`.
  Le premier entrepôt devient défaut automatiquement.
- Endpoints : `GET/POST /warehouses/`, `GET/PATCH /warehouses/{id}/`,
  `POST /warehouses/{id}/set-default/` (verrou global, un seul défaut),
  `deactivate/` (refusé si défaut), `reactivate/`.

## 5. Stock — `/inventory/`

La partie la plus sensible du produit.

- `StockLevel` : cache dénormalisé (produit × entrepôt unique, `quantity >= 0`).
- `StockMovement` : **ledger immuable** (aucune route d'écriture hors
  entrée/sortie/transfert, pas de PATCH/DELETE). Raisons : `purchase`, `sale`,
  `adjustment`, `transfer`, `return_customer`, `return_supplier`, `loss`,
  `initial`, `other`.
- Endpoints :
  - `GET /inventory/stock-levels/` (filtres `product`, `warehouse`),
  - `GET /inventory/stock-levels/low-stock/` (qty < seuil produit),
  - `GET /inventory/movements/` (filtres `product`, `warehouse`,
    `movement_type`, `reason`, dates),
  - `POST /inventory/movements/in|out|transfer/`.
- Règles : pas de sortie à découvert (`InsufficientStockError`) ; transfert
  inter-entrepôts avec verrous par pk croissant (anti-deadlock) ; mouvement et
  niveau de stock créés **dans la même transaction** ; audit systématique.

## 6. Achats — `/purchases/orders/`

- `PurchaseOrder` (+ `PurchaseOrderLine`) : fournisseur obligatoire (doit être
  `is_supplier`), `warehouse` de destination, statuts voir workflow.
- Endpoints : `GET/POST`, `GET /{id}/`, `POST /{id}/confirm/`
  (`purchases.edit`), `POST /{id}/receive/` (`purchases.receive`),
  `POST /{id}/cancel/`.
- `record_purchase_receipt` : verrouille les lignes, incrémente
  `quantity_received`, **crée le mouvement de stock d'entrée** (`reason=purchase`,
  `reference=order_number`) dans la même transaction, recalcule le statut.

## 7. Ventes — `/sales/orders/`

Miroir des achats.

- `SalesOrder` (+ `SalesOrderLine`) : client doit être `is_customer`,
  `warehouse` source.
- Endpoints : `GET/POST`, `GET /{id}/`, `POST /{id}/confirm/`, `POST /{id}/deliver/`,
  `POST /{id}/cancel/`.
- **Contrôle d'encours** : à la confirmation, si `credit_limit > 0`, la somme
  des commandes non soldées + la commande courante ne doit pas dépasser la
  limite (approximation V1, à affiner avec l'encours facturé réel).
- `record_sales_delivery` : met à jour `quantity_delivered` + sortie de stock
  (`reason=sale`) dans la même transaction ; stock insuffisant → refus.

## 8. Facturation — `/billing/`

- `Invoice` (+ `InvoiceLine`) : générée manuellement ou depuis une commande de
  vente ; échéance = `issue_date + payment_terms_days` du client ; totaux
  calculés à la volée (`total_amount`, `amount_paid`, `balance_due`,
  `is_overdue`).
- `Payment` : **immuable**, méthodes `cash`, `bank_transfer`, `check`,
  `mobile_payment`, `other`.
- Endpoints : `GET/POST /billing/invoices/`,
  `POST /billing/invoices/from-order/` (commande au moins partiellement livrée,
  jamais déjà facturée, ne facture que les quantités livrées),
  `GET /{id}/`, `POST /{id}/issue/`, `POST /{id}/cancel/`,
  `POST /{id}/payments/`.
- `record_payment` : **verrouille la facture** (`select_for_update`) pour
  interdire un paiement > solde ; recalcule `paid`/`partially_paid`.
- **Écritures comptables automatiques** (silencieuses si PCM absent) : émission
  → débit client (342) / crédit ventes (701) au journal VENTES ; paiement →
  débit trésorerie (5161/5141) / crédit client au journal Caisse ou Banque.

## 9. Coopératives — `/cooperatives/`

- `Cooperative` : **le tenant racine** (n'hérite pas de `TenantBaseModel`).
  Identité, infos légales marocaines (ICE 15 chiffres, RC), `default_language`,
  **abonnement** : `subscription_plan` (`trial`/`basic`/`pro`),
  `subscription_status`, `trial_ends_at` (**14 jours**), `is_trial_expired`.
- Endpoints :
  - `POST /cooperatives/register/` — **public**, throttle 5/h/IP, atomique
    (coopérative + OWNER dans la même transaction), retourne directement des
    JWT.
  - `GET/PATCH /cooperatives/me/` (écriture OWNER/ADMIN).
  - `POST /cooperatives/me/logo/`.
- `generate_unique_slug()` : slug + suffixe numérique en cas de collision.

## 10. Équipe & invitations — `/users/`

- `Invitation` : token opaque 256 bits à usage unique, expiration **7 jours**,
  une seule invitation `pending` par (coopérative, email).
- Endpoints : `GET /users/`, `PATCH /users/{id}/role/`,
  `POST /users/{id}/deactivate|reactivate/`, `GET/POST /users/invitations/`,
  `DELETE /users/invitations/{id}/`, `POST /users/invitations/accept/` (public).
- Règles centralisées (`services.py`) : **garde-fou du dernier OWNER** (ni
  rétrogradation ni désactivation) ; on ne change pas son propre rôle ; seul un
  OWNER gère les OWNER ; pas d'invitation d'un compte déjà membre ou déjà en
  attente. Toutes les actions sont journalisées.

## 11. Rôles & permissions — `/roles/permissions/`

Voir [architecture.md — RBAC](architecture.md#rbac--rôles--permissions).

## 12. Tableau de bord — `/dashboard/summary/`

`GET /dashboard/summary/?date_from&date_to` (défaut : mois courant, permission
`reports.view`). KPIs : membres actifs/totaux, clients/fournisseurs, commandes
par statut, revenus facturés sur période, dépenses confirmées, **valeur du
stock** + produits sous-seuil, encours clients, factures en retard, encaissé.

## 13. Reporting — `/reporting/`

- `GET /reporting/invoices/{id}/pdf/` — facture PDF (ReportLab) : logo, TVA
  20 % (défaut Maroc), identifiants légaux, coordonnées bancaires, pénalités de
  retard, pagination, statut coloré.
- Exports Excel (OpenPyXL) : `exports/members/` → `membres.xlsx`,
  `exports/stock-movements/?date_from&date_to`, `exports/sales-orders/`.
- Permissions : PDF = `billing.view` ; exports = `reports.view`.

## 14. Audit — `/audit/logs/`

`AuditLog` : journal **immuable** (INSERT only). `action` au format
`<module>.<événement>` (`stock.in`, `user.role_changed`, `invoice.issued`),
`target_type/id/repr`, `metadata` JSON, `ip_address`.
`GET /audit/logs/` — lecture seule, filtres `action` (istartswith), `actor`,
`target_type`, `target_id`, dates. Permission `audit.view`.
`log_activity()` est appelé **dans les transactions métier** (échec de log =
échec de l'action, cohérence assumée).

## 15. Comptabilité — `/accounting/`

- `Account` : plan comptable **PCM marocain** (classes 1→7), hiérarchique,
  `is_system` non supprimable.
- `Journal` : `JV` (ventes), `JA` (achats), `CAI` (caisse), `BQ` (banque),
  `OD` (opérations diverses).
- `AccountingEntry` (+ lignes) : `entry_number` auto `<JOURNAL>-YYYY-NNNNN`,
  `period` (YYYY-MM), `is_posted` (brouillon → validé), équilibre
  débit/crédit exigé.
- Endpoints : `GET/POST /accounting/accounts/` (POST = sous-compte personnalisé),
  `GET /accounting/journals/`, `GET/POST /accounting/entries/`,
  `POST /accounting/entries/{id}/post/` (`accounting.post`),
  `GET /accounting/ledger/?account_id&date_from&date_to` (grand livre, **solde
  progressif** selon le type de compte), `GET /accounting/trial-balance/?period=`,
  `GET /accounting/dashboard/`, `GET /accounting/financial-statements/?period=`
  (CPC + Bilan condensé).
- **Règle fondamentale** : aucune écriture non équilibrée n'est validée ;
  minimum 2 lignes ; brouillons non comptabilisables.

## Commandes de gestion

```bash
# Coopérative de démo avec cycle métier complet (login : owner@demo.ma / Demo1234!)
python manage.py seed_demo_data [--reset]

# Charger le plan comptable marocain + 5 journaux pour une coopérative
python manage.py load_pcm --cooperative-id <uuid>
```
