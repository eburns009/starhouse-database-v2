#!/usr/bin/env python3
"""
SECURITY FIX: Remove hardcoded DATABASE_URL from all scripts

This script automatically replaces hardcoded credentials with
secure environment variable loading.

CRITICAL: Run this BEFORE committing any code!

Usage:
    python3 scripts/fix_hardcoded_credentials.py --dry-run  # Preview changes
    python3 scripts/fix_hardcoded_credentials.py --execute  # Apply changes

Author: Security Fix
Date: 2025-11-17
"""

import os
import re
import sys
import argparse
from pathlib import Path


class CredentialFixer:
    """Removes hardcoded credentials from Python scripts."""

    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.stats = {
            'files_scanned': 0,
            'files_with_credentials': 0,
            'files_fixed': 0,
            'errors': 0
        }

    def find_scripts_with_credentials(self, scripts_dir: Path):
        """Find all Python scripts with hardcoded DATABASE_URL."""
        pattern = re.compile(r"DATABASE_URL\s*=\s*['\"]postgresql://[^'\"]+['\"]")

        files_with_creds = []

        for py_file in scripts_dir.glob('*.py'):
            self.stats['files_scanned'] += 1

            try:
                content = py_file.read_text()

                if pattern.search(content):
                    files_with_creds.append(py_file)
                    self.stats['files_with_credentials'] += 1

            except Exception as e:
                print(f"[ERROR] Failed to read {py_file.name}: {e}")
                self.stats['errors'] += 1

        return files_with_creds

    def fix_file(self, file_path: Path):
        """Remove hardcoded credentials from a single file."""
        try:
            content = file_path.read_text()
            original_content = content

            # Pattern to match hardcoded DATABASE_URL
            pattern = re.compile(
                r"DATABASE_URL\s*=\s*['\"]postgresql://[^'\"]+['\"]"
            )

            # Check if file already imports from db_config
            has_db_config_import = 'from db_config import get_database_url' in content

            # Replace hardcoded URL
            if pattern.search(content):
                # Add import at the top if not present
                if not has_db_config_import:
                    # Find the right place to add import (after other imports)
                    import_pattern = re.compile(r'^(import |from )', re.MULTILINE)
                    matches = list(import_pattern.finditer(content))

                    if matches:
                        # Add after last import
                        last_import_end = matches[-1].end()
                        # Find end of line
                        next_newline = content.find('\n', last_import_end)
                        if next_newline != -1:
                            insert_pos = next_newline + 1
                            content = (
                                content[:insert_pos] +
                                'from db_config import get_database_url\n' +
                                content[insert_pos:]
                            )
                    else:
                        # No imports found, add at very top after shebang/docstring
                        if content.startswith('#!/usr/bin/env python3'):
                            first_line_end = content.find('\n') + 1
                            content = (
                                content[:first_line_end] +
                                '\nfrom db_config import get_database_url\n\n' +
                                content[first_line_end:]
                            )
                        else:
                            content = 'from db_config import get_database_url\n\n' + content

                # Replace hardcoded URL with function call
                content = pattern.sub('DATABASE_URL = get_database_url()', content)

                if content != original_content:
                    if not self.dry_run:
                        file_path.write_text(content)
                        print(f"[FIXED] {file_path.name}")
                        self.stats['files_fixed'] += 1
                    else:
                        print(f"[PREVIEW] Would fix {file_path.name}")
                        self.stats['files_fixed'] += 1

                    return True

            return False

        except Exception as e:
            print(f"[ERROR] Failed to fix {file_path.name}: {e}")
            self.stats['errors'] += 1
            return False

    def run(self):
        """Main execution."""
        print("\n" + "=" * 80)
        if self.dry_run:
            print("DRY RUN: Scanning for hardcoded credentials")
        else:
            print("EXECUTE: Removing hardcoded credentials")
        print("=" * 80)
        print()

        # Find scripts directory
        project_root = Path(__file__).parent.parent
        scripts_dir = project_root / 'scripts'

        # Find all files with hardcoded credentials
        files_to_fix = self.find_scripts_with_credentials(scripts_dir)

        print(f"Found {len(files_to_fix)} files with hardcoded credentials:")
        print()

        # Fix each file
        for file_path in sorted(files_to_fix):
            self.fix_file(file_path)

        # Print summary
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Files scanned:            {self.stats['files_scanned']}")
        print(f"Files with credentials:   {self.stats['files_with_credentials']}")
        print(f"Files fixed:              {self.stats['files_fixed']}")
        print(f"Errors:                   {self.stats['errors']}")
        print("=" * 80)

        if self.dry_run:
            print()
            print("This was a DRY RUN - no files were modified")
            print("Run with --execute to apply changes")
            print()
        else:
            print()
            print("✓ All files have been updated!")
            print()
            print("Next steps:")
            print("1. Copy .env.example to .env:")
            print("   cp .env.example .env")
            print()
            print("2. Edit .env and add your database credentials")
            print()
            print("3. Install python-dotenv:")
            print("   pip install python-dotenv")
            print()
            print("4. Test a script to verify it works:")
            print("   python3 scripts/db_config.py")
            print()

        return 0 if self.stats['errors'] == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description='Remove hardcoded DATABASE_URL from scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute fix (default is dry-run)'
    )

    args = parser.parse_args()

    fixer = CredentialFixer(dry_run=not args.execute)
    return fixer.run()


if __name__ == '__main__':
    sys.exit(main())
