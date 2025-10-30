# StarHouse Database V2

FAANG-grade contact database with UUID architecture, designed for Supabase.

## Overview

This repository contains a modern contact management database system with:
- UUID-based architecture for scalability
- Normalized relational design
- Support for tags, products, subscriptions, and transactions
- Sample data for testing
- Production-ready schema

## Project Structure

```
starhouse-database-v2/
├── schema/          # Database schema files
├── data/
│   ├── production/  # Production CSV data files
│   └── samples/     # Sample data for testing
├── docs/            # Additional documentation
├── scripts/         # Python scripts for data processing
└── README.md        # This file
```

## Features

- **Contact Management**: Store and manage contact information with UUIDs
- **Tag System**: Flexible tagging system for categorizing contacts
- **Product Management**: Track products and contact-product relationships
- **Subscriptions**: Manage subscription tiers and contact subscriptions
- **Transactions**: Record transaction history linked to contacts
- **Data Integrity**: Foreign key constraints and proper indexing

## Quick Start

### Prerequisites

- Supabase account (or PostgreSQL 12+)
- Python 3.8+ (for data processing scripts)

### Setup

1. **Clone this repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/starhouse-database-v2.git
   cd starhouse-database-v2
   ```

2. **Apply the schema**
   - Navigate to your Supabase project
   - Go to SQL Editor
   - Copy and paste the schema from `schema/` directory
   - Execute the SQL

3. **Import data**
   - Start with sample data from `data/samples/` for testing
   - Use production data from `data/production/` when ready
   - Import via Supabase UI or CLI

## Database Schema

### Core Tables

- `v2_contacts`: Main contact information
- `v2_tags`: Tag definitions
- `v2_products`: Product catalog
- `v2_subscriptions`: Subscription tiers

### Relationship Tables

- `v2_contact_tags`: Many-to-many contact-tag relationships
- `v2_contact_products`: Many-to-many contact-product relationships
- `v2_transactions`: Transaction records linked to contacts

## Development

### Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt  # If requirements.txt exists
```

### Scripts

Scripts for data processing and migration are located in the `scripts/` directory.

## Current Status

**Phase**: Development / Initial Setup

**Completed**:
- [x] V2 schema design
- [x] Project structure setup
- [x] Git repository initialized

**Next Steps**:
- [ ] Add schema SQL files
- [ ] Add data files
- [ ] Add documentation
- [ ] Deploy to Supabase
- [ ] Test with sample data

## Contributing

This is a private project. For questions or issues, contact the project maintainer.

## License

Private - All Rights Reserved

---

**Last Updated**: 2024-10-30
