#!/usr/bin/env python3
"""
Generate TypeScript types from PostgreSQL schema
FAANG Standards: Automated type generation from single source of truth (database)
"""

import psycopg2
from pathlib import Path
from db_config import get_database_url

DATABASE_URL = get_database_url()

# PostgreSQL to TypeScript type mapping
PG_TO_TS_TYPES = {
    'text': 'string',
    'character varying': 'string',
    'varchar': 'string',
    'character': 'string',
    'uuid': 'string',
    'inet': 'string',
    'cidr': 'string',
    'macaddr': 'string',
    'integer': 'number',
    'int': 'number',
    'int2': 'number',
    'int4': 'number',
    'int8': 'number',
    'smallint': 'number',
    'bigint': 'number',
    'real': 'number',
    'float4': 'number',
    'float8': 'number',
    'double precision': 'number',
    'numeric': 'number',
    'decimal': 'number',
    'boolean': 'boolean',
    'bool': 'boolean',
    'timestamp with time zone': 'string',
    'timestamp without time zone': 'string',
    'timestamptz': 'string',
    'timestamp': 'string',
    'date': 'string',
    'time': 'string',
    'interval': 'string',
    'jsonb': 'Json',
    'json': 'Json',
    'bytea': 'string',
}

def get_ts_type(pg_type):
    """Convert PostgreSQL type to TypeScript type"""
    base_type = pg_type.lower().split('[')[0]  # Remove array notation
    ts_type = PG_TO_TS_TYPES.get(base_type, 'unknown')

    if '[]' in pg_type or 'ARRAY' in pg_type:
        return f'{ts_type}[]'
    return ts_type

def generate_staff_types():
    """Generate TypeScript types for staff_members table"""
    print("🔧 Generating TypeScript types from database schema...")
    print()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Get staff_members table schema
        cur.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'staff_members'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)

        columns = cur.fetchall()

        # Generate TypeScript interface
        ts_output = []
        ts_output.append("// Generated from PostgreSQL schema")
        ts_output.append("// DO NOT EDIT MANUALLY - Run generate_typescript_types.py to regenerate")
        ts_output.append("")
        ts_output.append("export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[]")
        ts_output.append("")
        ts_output.append("export type StaffRole = 'admin' | 'full_user' | 'read_only'")
        ts_output.append("")
        ts_output.append("export interface StaffMember {")

        for col_name, data_type, is_nullable, col_default in columns:
            ts_type = get_ts_type(data_type)
            nullable = " | null" if is_nullable == 'YES' else ""
            ts_output.append(f"  {col_name}: {ts_type}{nullable}")

        ts_output.append("}")
        ts_output.append("")

        # Generate Database interface
        ts_output.append("export interface Database {")
        ts_output.append("  public: {")
        ts_output.append("    Tables: {")
        ts_output.append("      staff_members: {")
        ts_output.append("        Row: StaffMember")
        ts_output.append("        Insert: Omit<StaffMember, 'added_at'>")
        ts_output.append("        Update: Partial<StaffMember>")
        ts_output.append("      }")
        ts_output.append("    }")
        ts_output.append("    Functions: {")
        ts_output.append("      is_admin: {")
        ts_output.append("        Args: Record<string, never>")
        ts_output.append("        Returns: boolean")
        ts_output.append("      }")
        ts_output.append("      can_edit: {")
        ts_output.append("        Args: Record<string, never>")
        ts_output.append("        Returns: boolean")
        ts_output.append("      }")
        ts_output.append("      get_user_role: {")
        ts_output.append("        Args: Record<string, never>")
        ts_output.append("        Returns: string")
        ts_output.append("      }")
        ts_output.append("      add_staff_member: {")
        ts_output.append("        Args: {")
        ts_output.append("          p_email: string")
        ts_output.append("          p_role?: StaffRole")
        ts_output.append("          p_display_name?: string")
        ts_output.append("          p_notes?: string")
        ts_output.append("        }")
        ts_output.append("        Returns: Json")
        ts_output.append("      }")
        ts_output.append("      change_staff_role: {")
        ts_output.append("        Args: {")
        ts_output.append("          p_email: string")
        ts_output.append("          p_new_role: StaffRole")
        ts_output.append("        }")
        ts_output.append("        Returns: Json")
        ts_output.append("      }")
        ts_output.append("      deactivate_staff_member: {")
        ts_output.append("        Args: {")
        ts_output.append("          p_email: string")
        ts_output.append("        }")
        ts_output.append("        Returns: Json")
        ts_output.append("      }")
        ts_output.append("    }")
        ts_output.append("  }")
        ts_output.append("}")
        ts_output.append("")

        # Write to file
        output_path = Path(__file__).parent.parent / 'starhouse-ui' / 'lib' / 'types' / 'staff.types.ts'
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write('\n'.join(ts_output))

        print(f"✅ Generated TypeScript types: {output_path}")
        print()
        print("📊 Generated types:")
        print("   - StaffRole (type union)")
        print("   - StaffMember (interface)")
        print("   - Database.public.Tables.staff_members (Row/Insert/Update)")
        print("   - Database.public.Functions (all helper functions)")
        print()
        print(f"📄 File size: {len('\\n'.join(ts_output))} bytes")
        print(f"📄 Total lines: {len(ts_output)}")
        print()

        return output_path

    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    output_path = generate_staff_types()
    print("✅ Type generation complete!")
    print()
    print("Next steps:")
    print("1. Import types in your React components:")
    print(f"   import {{ StaffMember, StaffRole, Database }} from '@/lib/types/staff.types'")
    print()
    print("2. Use with Supabase client:")
    print("   const supabase = createClient<Database>()")
    print()
    print("Ready for Phase 2: API Layer & React Hooks!")
