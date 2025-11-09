#!/bin/bash
# Database connection wrapper script
# Usage: ./db.sh "SELECT * FROM table;"

PGPASSWORD='***REMOVED***' psql \
  postgres://***REMOVED***@***REMOVED***:6543/postgres \
  "$@"
