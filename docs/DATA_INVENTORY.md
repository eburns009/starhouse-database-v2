# StarHouse Platform - Data Inventory

**Phase 1, Day 1 Audit**
**Date:** 2025-11-22
**Author:** Claude Code

---

## Executive Summary

The StarHouse database is a consolidation platform for 7 external systems (Kajabi, PayPal, Zoho, QuickBooks, Ticket Tailor, Mailchimp, Google Contacts). Current data inventory shows:

- **38 CSV files** across production, samples, and working directories
- **36 import/migration scripts** handling various data sources
- **28 database migrations** establishing schema
- **Core tables**: contacts, transactions, subscriptions, tags, products

---

## 1. CSV File Inventory

### Production Data Files (Primary Data)

| File | Size | Rows | Purpose |
|------|------|------|---------|
| v2_contacts.csv | 883 KB | 5,621 | Master contact records |
| v2_contact_tags.csv | 1.2 MB | 8,796 | Contact-tag relationships |
| v2_transactions.csv | 877 KB | 4,371 | Transaction history |
| transactions.csv | 1.1 MB | 4,379 | Original transaction export |
| v2_contact_products.csv | 176 KB | 1,353 | Contact-product relationships |
| v2_subscriptions.csv | 43 KB | 264 | Subscription records |
| v2_tags.csv | 9.6 KB | 98 | Tag definitions |
| v2_products.csv | 3.3 KB | 27 | Product catalog |

**Location:** `/data/production/`

### Working Data Files (Import/Processing)

| File | Size | Purpose |
|------|------|---------|
| mailing_list.csv | 136 KB | Active mailing list |
| validated_mailing_list.csv | 138 KB | USPS-validated addresses |
| mailing_list_good_addresses.csv | 242 KB | Confirmed good addresses |
| donors_us_ready_for_validation-output.csv | 356 KB | US donor data for NCOA |
| kajabi_full_enriched_export.csv | 359 KB | Enriched Kajabi contacts |
| truencoa_exceptions_corrected.csv | 91 KB | NCOA correction results |
| kajabi_subscriptions.csv | 50 KB | Kajabi subscription data |
| partners.csv | 23 KB | Partner organizations |
| paypal_subscriptions_analysis.csv | 17 KB | PayPal analysis output |

**Location:** `/data/` and `/` (root)

### Import Logs

| File | Size | Date | Purpose |
|------|------|------|---------|
| google_contacts_enrichment_*.csv | 57 KB | 2025-11-14 | Google enrichment log |
| google_addresses_import_*.csv | 8.2 KB | 2025-11-14 | Address import log |
| google_labels_import_*.csv | 2.0 KB | 2025-11-14 | Label import log |

**Location:** `/logs/`

### Sample Data (For Testing)

All v2_*_sample.csv files in `/data/samples/` (~1-2 KB each) - used for development/testing.

---

## 2. Import Scripts Inventory

### Weekly Import Scripts (Active)

| Script | Purpose | Source System |
|--------|---------|---------------|
| weekly_import_all.py | Master import orchestrator | All systems |
| weekly_import_all_v2.py | Updated import orchestrator | All systems |
| weekly_import_kajabi.py | Kajabi contact sync | Kajabi |
| weekly_import_kajabi_simple.py | Simplified Kajabi sync | Kajabi |
| weekly_import_kajabi_improved.py | Enhanced Kajabi sync | Kajabi |
| weekly_import_kajabi_v2.py | Latest Kajabi sync | Kajabi |
| weekly_import_paypal.py | PayPal transaction sync | PayPal |
| weekly_import_paypal_improved.py | Enhanced PayPal sync | PayPal |

### One-Time Import Scripts

| Script | Purpose | Source System |
|--------|---------|---------------|
| import_kajabi_data_v2.py | Full Kajabi data import | Kajabi |
| import_kajabi_subscriptions.py | Subscription import | Kajabi |
| import_kajabi_transactions.py | Transaction import | Kajabi |
| import_kajabi_transactions_optimized.py | Optimized transaction import | Kajabi |
| import_paypal_transactions.py | PayPal transaction import | PayPal |
| import_paypal_transactions_FIXED.py | Fixed PayPal import | PayPal |
| import_paypal_2024.py | 2024 PayPal data | PayPal |
| import_zoho_contacts.py | Zoho CRM contacts | Zoho |
| import_ticket_tailor.py | Event ticket data | Ticket Tailor |
| import_quickbooks_contacts.py | QuickBooks donor contacts | QuickBooks |

### Google Integration Scripts

| Script | Purpose |
|--------|---------|
| import_google_addresses.py | Address enrichment |
| import_google_labels_as_tags.py | Label to tag conversion |
| import_debbie_google_addresses.py | Staff-specific import |
| import_debbie_google_labels.py | Staff-specific import |

### Address Validation Scripts

| Script | Purpose |
|--------|---------|
| import_usps_validation.py | USPS address validation |
| import_usps_validation_safe.py | Safe mode validation |
| import_usps_validation_all.py | Bulk validation |
| import_usps_validation_shipping.py | Shipping validation |
| import_smarty_validation.py | SmartyStreets validation |
| import_ncoa_results.py | NCOA move results |
| import_ncoa_exceptions.py | NCOA exceptions |

### Migration Scripts

| Script | Purpose |
|--------|---------|
| migrate_additional_emails_to_table.py | Move emails to contact_emails table |
| migrate_paypal_emails.py | Migrate PayPal email associations |

### Analysis Scripts

| Script | Purpose |
|--------|---------|
| analyze_import_impact.py | Pre-import analysis |
| analyze_new_imports.py | New data analysis |
| check_mailchimp_imported.py | Mailchimp verification |
| verify_import_against_unsubscribed.py | Unsubscribe verification |
| verify_ticket_tailor_and_create_import.py | Ticket Tailor prep |

---

## 3. Database Schema Summary

### Core Tables (from migrations)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| contacts | Master contact records | id (UUID), email, first_name, last_name, address fields |
| contact_emails | Multi-email support | contact_id, email, is_primary, is_outreach, source |
| contact_tags | Tag relationships | contact_id, tag_id |
| contact_roles | Role tracking | contact_id, role, status, started_at |
| contact_notes | Staff notes | contact_id, note_type, content |
| external_identities | Cross-system IDs | contact_id, system, external_id |
| subscriptions | Subscription records | contact_id, status, amount, billing_cycle |
| transactions | Transaction history | contact_id, amount, source_system, transaction_date |
| products | Product catalog | name, product_type |

### Supporting Tables

| Table | Purpose |
|-------|---------|
| staff_members | Staff authentication |
| webhook_events | Webhook processing log |
| webhook_nonces | Replay protection |
| webhook_rate_limits | Rate limiting |
| mailing_list_exports | Export audit trail |

### Key Views

| View | Purpose |
|------|---------|
| v_membership_status | Real-time membership status |
| v_active_members | Current active members only |
| v_membership_metrics | Dashboard statistics |

---

## 4. Source System Mapping

### Data Flow: CSV → Table

| Source System | CSV Files | Target Table | Status |
|---------------|-----------|--------------|--------|
| **Kajabi** | v2_contacts.csv, kajabi_subscriptions.csv | contacts, subscriptions | Active |
| **PayPal** | transactions.csv | transactions | Active |
| **Ticket Tailor** | (webhook) | transactions | Active |
| **Zoho** | (direct import) | contacts | One-time |
| **QuickBooks** | (from "kajabi 3 files review/") | contacts | One-time |
| **Google Contacts** | (API) | contact_emails, tags | Enrichment |
| **Mailchimp** | (referenced) | contacts | Verified |

### Source System Tags in Database

The `source_system` field in transactions tracks:
- `kajabi` - Kajabi payments
- `paypal` - PayPal payments
- `ticket_tailor` - Event tickets

The `source` field in contact_emails tracks:
- `kajabi`, `paypal`, `ticket_tailor`, `zoho`, `quickbooks`, `mailchimp`, `manual`, `import`

---

## 5. Key Findings & Observations

### Data Volume Summary

- **~5,600 contacts** in master contact list
- **~4,400 transactions** (both Kajabi and PayPal combined)
- **~260 active subscriptions**
- **~8,800 contact-tag relationships**
- **~100 unique tags**

### Import Script Proliferation

**Concern:** Multiple versions of same import scripts exist (e.g., 6 versions of Kajabi import). This indicates iteration but may cause confusion about which script is authoritative.

**Recommendation:** Document which scripts are currently in use vs deprecated.

### Data Quality Indicators

1. **Address validation in progress** - Multiple USPS/NCOA validation scripts and result files
2. **Multi-email support implemented** - contact_emails table with source tracking
3. **Transaction provenance** - source_system field distinguishes Kajabi vs PayPal vs Ticket Tailor

### Missing/Incomplete Areas

1. **Donors module not yet built** - QuickBooks import script exists but donors table doesn't
2. **JotForm integration pending** - No JotForm import scripts found
3. **Database row counts not directly accessible** - Need Supabase connection to get actual counts

---

## 6. Recommendations for Next Steps

### Immediate Actions (Day 2-3)

1. **Run database audit query** to get actual table row counts:
```sql
SELECT tablename, n_live_tup
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

2. **Document active vs deprecated scripts** - Create SCRIPT_STATUS.md marking each as active/deprecated

3. **Verify data integrity** - Compare CSV row counts to database counts

### For Donors Module Planning

The existing infrastructure shows:
- **QuickBooks import script exists** (`import_quickbooks_contacts.py`)
- **Transaction tracking works** (source_system field)
- **Contact deduplication logic present** (email-based matching)

Key question: Where does JotForm donation data live, and how will it integrate with QuickBooks data?

---

## 7. File Location Summary

```
/workspaces/starhouse-database-v2/
├── data/
│   ├── production/          # Primary data exports (v2_*.csv)
│   ├── samples/            # Test data samples
│   └── current/            # Current working files
├── scripts/                # All import/migration scripts
├── logs/                   # Import logs with timestamps
├── supabase/
│   └── migrations/         # Database schema migrations
└── docs/
    └── DATA_INVENTORY.md   # This file
```

---

**End of Data Inventory Report**
