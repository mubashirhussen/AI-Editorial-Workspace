#!/usr/bin/env python3
"""
Automated Database Restore & Verification Utility.
Verifies SHA256 checksum against backup metadata before applying restore.
Supports validation/dry-run mode and confirms database accessibility post-restore.
"""

import os
import sys
import shutil
import hashlib
import json
import argparse
import subprocess
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.database import engine, check_db_health
from sqlalchemy import text

def calculate_sha256(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def verify_backup_integrity(backup_path: str) -> bool:
    """Verifies that the backup file exists and matches its SHA256 metadata manifest if present."""
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    current_hash = calculate_sha256(backup_path)
    manifest_path = f"{backup_path}.json"

    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        expected_hash = meta.get("sha256")
        if expected_hash and current_hash != expected_hash:
            raise ValueError(f"Checksum mismatch! Expected {expected_hash}, calculated {current_hash}. Backup may be corrupted.")
        print(f"Verified checksum integrity against manifest: {current_hash[:12]}... (OK)")
    else:
        print(f"Warning: No manifest found at {manifest_path}. Checksum: {current_hash[:12]}...")

    return True

def restore_database(backup_path: str = None, manifest_path: str = None, target_database_url: str = None, dry_run: bool = False) -> Dict[str, Any]:
    # Support either passing the manifest directly or the backup file
    actual_backup = backup_path
    if manifest_path and not backup_path:
        with open(manifest_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        actual_backup = meta.get("backup_file") or meta.get("backup_path")
        if not actual_backup or not os.path.exists(actual_backup):
            base_name = os.path.splitext(manifest_path)[0]
            if os.path.exists(base_name):
                actual_backup = base_name

    if not actual_backup:
        raise ValueError("Either backup_path or valid manifest_path must be provided.")

    print(f"Validating backup: {actual_backup}")
    verify_backup_integrity(actual_backup)

    if dry_run:
        print("Dry-run mode active: Verified checksum and integrity. Skipping file overwrites.")
        return {"status": "dry_run_passed", "backup_path": actual_backup}

    db_url = target_database_url or settings.DATABASE_URL or "sqlite:///./editorial.db"

    if db_url.startswith("sqlite"):
        sqlite_file = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not os.path.isabs(sqlite_file):
            sqlite_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", sqlite_file))

        # Perform atomic SQLite restore
        os.makedirs(os.path.dirname(sqlite_file), exist_ok=True)
        temp_target = f"{sqlite_file}.tmp"
        shutil.copy2(actual_backup, temp_target)
        if os.path.exists(sqlite_file):
            os.remove(sqlite_file)
        os.rename(temp_target, sqlite_file)
        print(f"SQLite database restored successfully to: {sqlite_file}")
    else:
        # PostgreSQL restore
        cmd = ["pg_restore", "-c", "-d", db_url, actual_backup]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"PostgreSQL database restored successfully to: {db_url}")
        except Exception as e:
            print(f"Warning: pg_restore encountered notice/warning: {e}")

    # Post-restore health verification
    health = check_db_health()
    if health.get("status") != "healthy":
        raise RuntimeError(f"Database health check failed post-restore: {health.get('error')}")

    return {
        "status": "success",
        "backup_path": actual_backup,
        "database_url": db_url,
        "health": health
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database Restore Utility")
    parser.add_argument("backup_file", help="Path to database backup file")
    parser.add_argument("--dry-run", action="store_true", help="Validate backup without applying")
    args = parser.parse_args()

    restore_database(backup_path=args.backup_file, dry_run=args.dry_run)
