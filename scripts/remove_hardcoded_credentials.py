#!/usr/bin/env python3
"""
Script to remove hardcoded credentials from all Python files.
This is a one-time cleanup script.
"""

import os
import re
import sys
from pathlib import Path

# The hardcoded credential patterns to remove
PATTERNS_TO_REPLACE = [
    # Pattern 1: postgresql:// with hardcoded credentials
    (
        re.compile(
            r"DB_CONNECTION = os\.environ\.get\(\s*"
            r"['\"]DATABASE_URL['\"],\s*"
            r"['\"]postgresql://postgres\.lnagadkqejnopgfxwlkb:***REMOVED***@aws-1-us-east-2\.pooler\.supabase\.com:6543/postgres['\"]\s*"
            r"\)",
            re.MULTILINE | re.DOTALL
        ),
        "# Database connection - NO DEFAULTS, fails fast if missing\nDB_CONNECTION = get_database_url()"
    ),
    # Pattern 2: postgres:// with hardcoded credentials
    (
        re.compile(
            r"DB_CONNECTION = os\.environ\.get\(\s*"
            r"['\"]DATABASE_URL['\"],\s*"
            r"['\"]postgres://postgres\.lnagadkqejnopgfxwlkb:***REMOVED***@aws-1-us-east-2\.pooler\.supabase\.com:6543/postgres['\"]\s*"
            r"\)",
            re.MULTILINE | re.DOTALL
        ),
        "# Database connection - NO DEFAULTS, fails fast if missing\nDB_CONNECTION = get_database_url()"
    ),
    # Pattern 3: Inline connection strings
    (
        re.compile(
            r"psycopg2\.connect\(\s*"
            r"os\.environ\.get\(\s*"
            r"['\"]DATABASE_URL['\"],\s*"
            r"['\"]postgresql://postgres\.lnagadkqejnopgfxwlkb:***REMOVED***@[^'\"]+['\"]\s*"
            r"\)",
            re.MULTILINE | re.DOTALL
        ),
        "psycopg2.connect(\n        get_database_url()"
    ),
]


def has_secure_config_import(content: str) -> bool:
    """Check if file already imports secure_config."""
    return 'from secure_config import' in content or 'import secure_config' in content


def add_secure_config_import(content: str) -> str:
    """Add secure_config import after other imports."""
    # Find the last import statement
    lines = content.split('\n')
    last_import_idx = -1

    for idx, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            # Skip the sys.path.insert if it exists
            if 'sys.path.insert' not in line and 'from secure_config' not in line:
                last_import_idx = idx

    if last_import_idx >= 0:
        # Insert after last import and a blank line
        insert_idx = last_import_idx + 1

        # Add sys.path setup and import
        new_lines = (
            "\n# Add scripts directory to path for imports\n"
            "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
            "from secure_config import get_database_url\n"
        )

        lines.insert(insert_idx, new_lines)
        return '\n'.join(lines)

    return content


def process_file(file_path: Path) -> tuple[bool, str]:
    """
    Process a single Python file to remove hardcoded credentials.

    Returns:
        (modified, message) - Whether file was modified and a message
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        content = original_content
        modified = False

        # Check if this file has hardcoded credentials
        has_hardcoded = '***REMOVED***' in content

        if not has_hardcoded:
            return False, "No hardcoded credentials found"

        # Add secure_config import if not present
        if not has_secure_config_import(content):
            content = add_secure_config_import(content)
            modified = True

        # Replace all credential patterns
        for pattern, replacement in PATTERNS_TO_REPLACE:
            if pattern.search(content):
                content = pattern.sub(replacement, content)
                modified = True

        # Verify credentials are removed
        if '***REMOVED***' in content:
            return False, "WARNING: Credentials still present after replacement"

        # Write back if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "✅ Credentials removed"

        return False, "No changes needed"

    except Exception as e:
        return False, f"ERROR: {e}"


def main():
    """Main function."""
    scripts_dir = Path(__file__).parent

    print("Removing hardcoded credentials from Python scripts...")
    print("=" * 70)

    # Find all Python files with hardcoded credentials
    modified_count = 0
    error_count = 0
    skipped_files = ['remove_hardcoded_credentials.py', 'secure_config.py']

    for py_file in scripts_dir.glob('*.py'):
        if py_file.name in skipped_files:
            continue

        # Check if file has hardcoded credentials
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                if '***REMOVED***' not in f.read():
                    continue
        except:
            continue

        modified, message = process_file(py_file)

        if modified:
            print(f"✅ {py_file.name:40s} {message}")
            modified_count += 1
        elif "ERROR" in message or "WARNING" in message:
            print(f"❌ {py_file.name:40s} {message}")
            error_count += 1
        else:
            print(f"⏭️  {py_file.name:40s} {message}")

    print("=" * 70)
    print(f"Modified: {modified_count} files")
    if error_count > 0:
        print(f"Errors: {error_count} files")
        sys.exit(1)
    else:
        print("✅ All credentials removed successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main()
