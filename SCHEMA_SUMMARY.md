# StarHouse Database Schema Summary

**Generated:** 2025-11-27
**Status:** Diagnostic Only (No Fixes)

---

## 1. TABLE INVENTORY

| Table | Purpose | Row Count | Primary Key |
|-------|---------|-----------|-------------|
| `contacts` | Central contact registry - master list of all contacts across all systems | Unknown | `id` (UUID) |
| `tags` | Reusable categorization labels for contacts | Unknown | `id` (UUID) |
| `products` | Courses, memberships, events, and services offered | Unknown | `id` (UUID) |
| `contact_tags` | Junction: Contacts ↔ Tags (many-to-many) | Unknown | `id` (UUID) |
| `contact_products` | Junction: Contacts ↔ Products (access/purchase history) | Unknown | `id` (UUID) |
| `subscriptions` | Recurring subscription records with lifecycle tracking | Unknown | `id` (UUID) |
| `transactions` | Complete transaction history with payment details | Unknown | `id` (UUID) |
| `events` | Event details from Ticket Tailor integration | Unknown | `id` (UUID) |
| `event_registrations` | Ticket purchases / event registrations | Unknown | `id` (UUID) |
| `webhook_events` | Audit trail and idempotency tracking for webhooks | Unknown | `id` (UUID) |
| `webhook_rate_limits` | Token bucket rate limiting for webhooks | Unknown | `(source, bucket_key)` (composite) |
| `webhook_nonces` | Prevents intra-window replay attacks | Unknown | `id` (UUID) |
| `contact_emails` | Multi-email support per contact with source tracking | Unknown | `id` (UUID) |
| `external_identities` | Cross-system identity reconciliation (Kajabi, PayPal, etc.) | Unknown | `id` (UUID) |
| `contact_roles` | Time-bound role tracking (member, donor, volunteer, etc.) | Unknown | `id` (UUID) |
| `contact_notes` | Staff notes, call logs, meeting notes | Unknown | `id` (UUID) |
| `audit_log` | Append-only audit trail for all data modifications | Unknown | `id` (UUID) |
| `jobs` | Background job queue for long-running operations | Unknown | `id` (UUID) |
| `saved_views` | User-saved table views with filters/sorts/columns | Unknown | `id` (UUID) |
| `health_check_log` | Historical health check results for trending | Unknown | `id` (UUID) |
| `membership_products` | Referenced in RLS policies (schema not found) | Unknown | Unknown |
| `dlq_events` | Dead letter queue (referenced in RLS, schema not found) | Unknown | Unknown |

---

## 2. RELATIONSHIPS

### Foreign Key Relationships (Parent → Child)

| Parent Table | Child Table | FK Column | ON DELETE |
|--------------|-------------|-----------|-----------|
| `contacts` | `contact_tags` | `contact_id` | CASCADE |
| `contacts` | `contact_products` | `contact_id` | CASCADE |
| `contacts` | `subscriptions` | `contact_id` | RESTRICT |
| `contacts` | `transactions` | `contact_id` | RESTRICT |
| `contacts` | `event_registrations` | `contact_id` | CASCADE |
| `contacts` | `webhook_events` | `contact_id` | SET NULL |
| `contacts` | `contact_emails` | `contact_id` | CASCADE |
| `contacts` | `external_identities` | `contact_id` | CASCADE |
| `contacts` | `contact_roles` | `contact_id` | CASCADE |
| `contacts` | `contact_notes` | `contact_id` | CASCADE |
| `tags` | `contact_tags` | `tag_id` | CASCADE |
| `products` | `contact_products` | `product_id` | CASCADE |
| `products` | `subscriptions` | `product_id` | RESTRICT |
| `products` | `transactions` | `product_id` | RESTRICT |
| `products` | `events` | `kajabi_product_id` | SET NULL |
| `subscriptions` | `transactions` | `subscription_id` | SET NULL |
| `subscriptions` | `webhook_events` | `subscription_id` | SET NULL |
| `transactions` | `webhook_events` | `transaction_id` | SET NULL |
| `transactions` | `event_registrations` | `transaction_id` | SET NULL |
| `events` | `event_registrations` | `event_id` | CASCADE |

### How Contacts Connect to Related Entities

```
                        ┌─────────────────────┐
                        │      contacts       │
                        │   (Central Entity)  │
                        └─────────┬───────────┘
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    │                             │                             │
    ▼                             ▼                             ▼
┌───────────┐            ┌────────────────┐           ┌───────────────────┐
│  donors   │            │  transactions  │           │   memberships     │
│ (via tags │◄──────────►│  (contact_id)  │           │  (subscriptions)  │
│  & views) │            │                │           │   (contact_id)    │
└───────────┘            └────────────────┘           └───────────────────┘
                                  │
                                  ▼
                         ┌────────────────┐
                         │     events     │
                         │ (via event_    │
                         │ registrations) │
                         └────────────────┘
```

**Contact Connections:**
- **Donors**: Identified via tags, transactions with donation products, and donor-specific views
- **Transactions**: Direct FK (`transactions.contact_id → contacts.id`)
- **Memberships**: Via `subscriptions` table (`subscriptions.contact_id → contacts.id`)
- **Events**: Via `event_registrations` junction table

### Junction/Linking Tables

| Junction Table | Links | Unique Constraint |
|----------------|-------|-------------------|
| `contact_tags` | `contacts` ↔ `tags` | `(contact_id, tag_id)` |
| `contact_products` | `contacts` ↔ `products` | `(contact_id, product_id)` |
| `event_registrations` | `contacts` ↔ `events` | `(event_id, contact_id, ticket_tailor_booking_id)` |

---

## 3. CONSTRAINTS & INDEXES

### Unique Constraints

| Table | Constraint/Index | Columns | Notes |
|-------|------------------|---------|-------|
| `contacts` | `ux_contacts_email` | `email` | Case-insensitive via CITEXT |
| `contacts` | `idx_contacts_kajabi_id_unique` | `kajabi_id` | Partial (WHERE NOT NULL) |
| `contacts` | `idx_contacts_kajabi_member_id_unique` | `kajabi_member_id` | Partial |
| `contacts` | `idx_contacts_paypal_payer_id_unique` | `paypal_payer_id` | Partial |
| `contacts` | `idx_contacts_zoho_id_unique` | `zoho_id` | Partial |
| `contacts` | `idx_contacts_ticket_tailor_id_unique` | `ticket_tailor_id` | Partial |
| `tags` | `ux_tags_name_norm` | `name_norm` | Normalized name |
| `products` | `ux_products_name_norm` | `name_norm` | Normalized name |
| `products` | `idx_products_kajabi_offer_id_unique` | `kajabi_offer_id` | Partial |
| `subscriptions` | `idx_subscriptions_kajabi_subscription_id_unique` | `kajabi_subscription_id` | Partial |
| `subscriptions` | `idx_subscriptions_paypal_subscription_reference_unique` | `paypal_subscription_reference` | Partial |
| `transactions` | `ux_transactions_source_external` | `(source_system, external_transaction_id)` | Partial - canonical idempotency |
| `transactions` | `idx_transactions_kajabi_transaction_id_unique` | `kajabi_transaction_id` | Partial (DEPRECATED) |
| `events` | Inline | `ticket_tailor_event_id` | Unique |
| `event_registrations` | Inline | `ticket_tailor_booking_id` | Unique |
| `webhook_events` | `uq_webhook_events_provider_event` | `(source, provider_event_id)` | Race condition prevention |
| `webhook_nonces` | `uq_webhook_nonces_source_nonce` | `(source, nonce)` | Replay prevention |
| `contact_emails` | `ux_contact_emails_one_primary` | `contact_id` WHERE `is_primary` | One primary per contact |
| `contact_emails` | `ux_contact_emails_one_outreach` | `contact_id` WHERE `is_outreach` | One outreach per contact |
| `contact_emails` | `ux_contact_emails_unique_per_contact` | `(contact_id, email)` | No duplicate emails per contact |
| `external_identities` | `ux_external_identities_system_id` | `(system, external_id)` | Unique external ID per system |
| `external_identities` | `ux_external_identities_contact_system` | `(contact_id, system)` | One system ID per contact |
| `contact_roles` | `ux_contact_roles_unique_active` | `(contact_id, role)` WHERE `status = 'active'` | One active role per type |

### Key Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| `contacts` | `idx_contacts_source_system` | Filter by source |
| `contacts` | `idx_contacts_email_subscribed` | Email marketing lists |
| `contacts` | `idx_contacts_paypal_email` | PayPal email lookups |
| `contacts` | `idx_contacts_name_match` | Name-based matching |
| `transactions` | `idx_transactions_contact_date` | Contact transaction history |
| `transactions` | `idx_transactions_source_date` | Source-based reporting |
| `transactions` | `idx_transactions_contact_amount_date` | Duplicate detection |
| `subscriptions` | `idx_subscriptions_next_billing` | Billing reminders |
| `subscriptions` | `idx_subscriptions_active` | Active subscription lookups |
| `webhook_events` | `idx_webhook_events_payload_hash` | Replay attack detection |
| `webhook_events` | `idx_webhook_events_failed` | Failed webhook monitoring |
| `contact_emails` | `idx_contact_emails_email_trgm` | Fuzzy email search (trigram) |
| `contact_notes` | `idx_contact_notes_content_fts` | Full-text search |

### Missing Constraints Per ENGINEERING_STANDARDS.md

| Issue | Tables Affected | Standard Violated |
|-------|-----------------|-------------------|
| **Missing `deleted_at` column** | `events`, `event_registrations`, `webhook_events`, `contact_emails`, `external_identities`, `contact_roles`, `contact_notes` | "Soft-delete (deleted_at) over hard delete" |
| **Missing `updated_at` triggers** | `contact_tags`, `contact_products` | "Timestamps: created_at, updated_at" |
| **Transactions allow hard delete** | `transactions` | "Soft-delete over hard delete" - has `deleted_at` via migration but DELETE CASCADE not blocked |

---

## 4. AUTH/RLS STATUS

### Tables with RLS Enabled

| Table | RLS Enabled | Notes |
|-------|-------------|-------|
| `contacts` | ✅ Yes | Staff + service_role full access |
| `transactions` | ✅ Yes | Staff + service_role full access |
| `subscriptions` | ✅ Yes | Staff + service_role full access |
| `products` | ✅ Yes | Staff + service_role full access |
| `tags` | ✅ Yes | Staff + service_role full access |
| `contact_tags` | ✅ Yes | Staff + service_role full access |
| `contact_products` | ✅ Yes | Staff + service_role full access |
| `membership_products` | ✅ Yes | Staff + service_role full access |
| `webhook_nonces` | ✅ Yes | Staff + service_role full access |
| `webhook_rate_limits` | ✅ Yes | Staff + service_role full access |
| `health_check_log` | ✅ Yes | Staff + service_role full access |
| `dlq_events` | ✅ Yes | Staff + service_role full access |
| `webhook_events` | ✅ Yes | **service_role only** (security) |
| `contact_emails` | ✅ Yes | Authenticated users + auth.uid() checks |
| `external_identities` | ✅ Yes | Authenticated users + auth.uid() checks |
| `contact_roles` | ✅ Yes | Authenticated users + auth.uid() checks |
| `contact_notes` | ✅ Yes | Author-based policies + privacy |
| `audit_log` | ✅ Yes | Append-only (no updates/deletes) |
| `jobs` | ✅ Yes | User owns their own jobs |
| `saved_views` | ✅ Yes | User owns their own views |
| `events` | ❓ Unknown | Not explicitly enabled in reviewed files |
| `event_registrations` | ❓ Unknown | Not explicitly enabled in reviewed files |

### RLS Policies Summary

**Security Model:** Simple Staff Access (3-5 trusted users)

| Role | Access Level | Use Case |
|------|--------------|----------|
| `authenticated` | Full CRUD on most tables | Staff UI access |
| `service_role` | Full CRUD on all tables | Backend scripts, webhooks |
| `postgres` | Bypasses RLS | Import scripts, migrations |
| `anon` | No access (revoked) | Public - blocked |

**Key Policies:**
- `staff_full_access` - Authenticated users get full access (simple model for small team)
- `service_role_full_access` - Backend operations unrestricted
- Anon access explicitly revoked on all tables

### Staff/Auth Table Structure

**No dedicated staff table exists.** Authentication relies on:
- Supabase Auth (`auth.users`)
- Simple model: any authenticated user = staff with full access
- Future plan documented in `FUTURE_RLS_MIGRATION.md` for role-based access when team grows >5-7

---

## 5. GAPS & ISSUES

### Tables Referenced But Missing Schema Definitions

| Table | Referenced In | Status |
|-------|---------------|--------|
| `membership_products` | RLS policies (`002c_rls_simple_staff_access.sql`) | **Schema file not found** |
| `dlq_events` | RLS policies, health monitoring | **Schema file not found** |

### Foreign Keys Without Constraints

| Issue | Details |
|-------|---------|
| `transactions.kajabi_transaction_id` | DEPRECATED field, unique index exists but field is overloaded across sources |
| Legacy external ID columns on `contacts` | `kajabi_id`, `zoho_id`, etc. have unique indexes but should migrate to `external_identities` table |

### Standards Violations

| Violation | Location | Standard |
|-----------|----------|----------|
| **Mutable field as lookup key** | `contacts.email` used for matching | "Never use mutable fields (email) as PK" - email is not PK but is unique key |
| **Missing soft delete** | Multiple tables lack `deleted_at` | "Soft-delete (deleted_at) over hard delete" |
| **Hard delete possible** | `event_registrations` has `ON DELETE CASCADE` | Could orphan audit trail |
| **Inconsistent source tracking** | `contacts.source_system` vs `external_identities.system` | Dual tracking mechanisms |
| **Deprecated fields not removed** | `transactions.kajabi_transaction_id`, `contacts.kajabi_id` etc. | Should migrate to normalized tables |

### Data Integrity Concerns

1. **Cross-source duplicate transactions**: Kajabi + PayPal can both create records for same purchase
   - Mitigated by: `v_potential_duplicate_transactions` view, `find_probable_duplicate_transaction()` function

2. **Name duplicates**: Monitoring shows potential duplicates by normalized name
   - Mitigated by: `v_database_health` view with duplicate count alerts

3. **Orphaned records possible**:
   - Transactions/subscriptions use `ON DELETE RESTRICT` (safe)
   - Contact sub-tables use `CASCADE` (could lose history on contact delete)

---

## 6. SUPABASE FEATURES IN USE

### Triggers Defined

| Trigger | Table | Function | Purpose |
|---------|-------|----------|---------|
| `contacts_set_updated_at` | `contacts` | `set_updated_at()` | Auto-update timestamp |
| `tags_set_updated_at` | `tags` | `set_updated_at()` | Auto-update timestamp |
| `products_set_updated_at` | `products` | `set_updated_at()` | Auto-update timestamp |
| `subscriptions_set_updated_at` | `subscriptions` | `set_updated_at()` | Auto-update timestamp |
| `transactions_set_updated_at` | `transactions` | `set_updated_at()` | Auto-update timestamp |
| `set_events_updated_at` | `events` | `set_updated_at()` | Auto-update timestamp |
| `set_event_registrations_updated_at` | `event_registrations` | `set_updated_at()` | Auto-update timestamp |
| `webhook_events_set_updated_at` | `webhook_events` | `set_updated_at()` | Auto-update timestamp |
| `contact_emails_set_updated_by` | `contact_emails` | `set_updated_by()` | Track who made changes |
| `external_identities_set_updated_by` | `external_identities` | `set_updated_by()` | Track who made changes |
| `contact_roles_set_updated_by` | `contact_roles` | `set_updated_by()` | Track who made changes |
| `contact_roles_set_ended_at` | `contact_roles` | `set_role_ended_at()` | Auto-set end date on deactivation |
| `contact_notes_set_updated_by` | `contact_notes` | `set_updated_by()` | Track who made changes |
| `contact_notes_set_author` | `contact_notes` | `set_note_author()` | Auto-set author from auth context |
| `jobs_set_updated_at` | `jobs` | `set_updated_at()` | Auto-update timestamp |
| `saved_views_set_updated_at` | `saved_views` | `set_updated_at()` | Auto-update timestamp |
| `ensure_single_default_view_trigger` | `saved_views` | `ensure_single_default_view()` | Enforce one default view |

### Database Functions

| Function | Purpose | Type |
|----------|---------|------|
| `set_updated_at()` | Update `updated_at` timestamp on row update | Trigger |
| `set_updated_by()` | Track user who modified record | Trigger |
| `set_note_author()` | Auto-populate note author from auth | Trigger |
| `set_role_ended_at()` | Auto-set end date on role deactivation | Trigger |
| `ensure_single_default_view()` | Enforce one default saved view per entity | Trigger |
| `is_current_member(uuid)` | Check if contact is active member | Helper |
| `get_membership_status(uuid)` | Get membership status string | Helper |
| `get_active_member_emails()` | Get emails for active members | Helper |
| `is_webhook_processed(text)` | Check webhook idempotency | Security |
| `is_replay_attack(timestamptz)` | Detect replay attacks | Security |
| `is_duplicate_payload(text, text)` | Detect duplicate payloads | Security |
| `is_nonce_used(text, text)` | Check if nonce was used | Security |
| `record_nonce(text, text)` | Record nonce atomically | Security |
| `process_webhook_atomically(...)` | Atomic webhook processing | Security |
| `get_webhook_stats(int)` | Webhook monitoring stats | Monitoring |
| `cleanup_old_webhook_events()` | Delete old webhook events | Maintenance |
| `cleanup_old_nonces()` | Delete old nonces | Maintenance |
| `checkout_rate_limit(...)` | Token bucket rate limiting | Security |
| `get_rate_limit_info(...)` | Rate limit debugging | Monitoring |
| `cleanup_stale_rate_limits()` | Clean stale rate limit entries | Maintenance |
| `test_rate_limiting()` | Self-test rate limiting | Testing |
| `daily_health_check()` | Comprehensive health check | Monitoring |
| `log_health_check()` | Store health check results | Monitoring |
| `find_probable_duplicate_transaction(...)` | Find cross-source duplicates | Data Quality |

### Views

| View | Purpose |
|------|---------|
| `v_potential_duplicate_contacts` | Contacts with same email (data quality) |
| `v_active_subscriptions` | Active subscriptions with contact info |
| `v_contact_summary` | Aggregated contact metrics |
| `v_upcoming_events` | Upcoming events with registration counts |
| `v_contact_events` | Contact event history |
| `v_membership_status` | Real-time membership status |
| `v_active_members` | Current active members only |
| `v_membership_metrics` | Membership dashboard stats |
| `v_failed_webhooks` | Recent failed webhooks |
| `v_webhook_security_alerts` | Security alerts (invalid signatures, replays) |
| `v_rate_limit_status` | Rate limit bucket status |
| `v_database_health` | Overall database health |
| `v_performance_metrics` | Database performance stats |
| `v_recent_health_alerts` | Recent health check failures |
| `v_active_contacts` | Non-deleted contacts |
| `v_active_products` | Non-deleted, active products |
| `v_potential_duplicate_transactions` | Detects transaction duplicates |
| `v_revenue_by_source` | Revenue report by source system |
| `v_transactions_missing_provenance` | Transactions missing source tracking |

### Extensions in Use

| Extension | Purpose |
|-----------|---------|
| `uuid-ossp` | UUID generation (`uuid_generate_v4()`) |
| `citext` | Case-insensitive text for emails |
| `pg_trgm` | Trigram indexing for fuzzy search |

### Custom Types (Enums)

| Type | Values |
|------|--------|
| `subscription_status` | `active`, `paused`, `canceled`, `expired`, `trial` |
| `payment_status` | `pending`, `completed`, `failed`, `refunded`, `disputed` |
| `transaction_type` | `purchase`, `subscription`, `refund`, `adjustment` |
| `job_status` | `pending`, `running`, `completed`, `failed`, `cancelled` |
| `job_type` | `bulk_import`, `bulk_export`, `bulk_merge`, `bulk_tag`, `bulk_delete`, `report_generation`, `data_cleanup` |

---

## Summary

The StarHouse database follows FAANG-grade architecture with:
- UUID primary keys throughout
- Comprehensive audit trails and triggers
- Row-Level Security with simple staff access model
- Webhook security (idempotency, rate limiting, replay protection)
- Multi-source contact reconciliation support

**Key Areas for Future Attention:**
1. Complete migration from legacy external ID columns to `external_identities` table
2. Add `deleted_at` soft-delete columns to remaining tables
3. Define missing table schemas (`membership_products`, `dlq_events`)
4. Enable RLS on `events` and `event_registrations` tables
5. Consider role-based RLS when team grows beyond 5-7 staff
