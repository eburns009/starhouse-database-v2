#!/bin/bash
# Database connection wrapper script
# Usage: ./db.sh -c "SELECT * FROM table;"
#
# SECURITY: No hardcoded credentials!
# Requires DATABASE_URL environment variable to be set.
# Set it in .env file or export it:
#   export DATABASE_URL='postgresql://user:pass@host:port/db'

# Load .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set" >&2
    echo "Set it in .env file or environment:" >&2
    echo "  export DATABASE_URL='postgresql://user:pass@host:port/db'" >&2
    echo "See .env.example for template" >&2
    exit 1
fi

# Connect to database using DATABASE_URL
psql "$DATABASE_URL" "$@"
