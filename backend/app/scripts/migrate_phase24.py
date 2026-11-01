import sqlite3
import os
import sys
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from backend.app.core.security import hash_password

DEFAULT_ORG_ID = "default-org-uuid-000000000000"
DEFAULT_USER_ID = "default-user-uuid-000000000000"

def migrate_database(db_path: str):
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Skipping.")
        return

    print(f"Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(36) PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255) NOT NULL DEFAULT '',
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);")

    # 2. Create organizations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(255) UNIQUE NOT NULL,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_organizations_slug ON organizations (slug);")

    # 3. Create organization_memberships table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organization_memberships (
        id VARCHAR(36) PRIMARY KEY,
        organization_id VARCHAR(36) NOT NULL,
        user_id VARCHAR(36) NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'EDITOR',
        joined_at DATETIME NOT NULL,
        FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_org_mem_org ON organization_memberships (organization_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_org_mem_user ON organization_memberships (user_id);")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_org_user ON organization_memberships (organization_id, user_id);")

    # 4. Create organization_invitations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organization_invitations (
        id VARCHAR(36) PRIMARY KEY,
        organization_id VARCHAR(36) NOT NULL,
        email VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'EDITOR',
        token VARCHAR(255) UNIQUE NOT NULL,
        invited_by_id VARCHAR(36),
        expires_at DATETIME NOT NULL,
        accepted_at DATETIME,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
        FOREIGN KEY(invited_by_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_org_inv_token ON organization_invitations (token);")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_org_inv_email ON organization_invitations (email);")

    # 5. Add organization_id column to research_projects if not present
    cursor.execute("PRAGMA table_info(research_projects);")
    columns = [row[1] for row in cursor.fetchall()]
    if "organization_id" not in columns:
        print("Adding organization_id column to research_projects...")
        cursor.execute("ALTER TABLE research_projects ADD COLUMN organization_id VARCHAR(36) REFERENCES organizations(id) ON DELETE CASCADE;")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_research_projects_org ON research_projects (organization_id);")

    # 6. Seed Default Organization & Owner
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor.execute("SELECT id FROM organizations WHERE id = ? OR slug = ?", (DEFAULT_ORG_ID, "default-workspace"))
    org_row = cursor.fetchone()
    if not org_row:
        print("Seeding default organization: Personal Workspace...")
        cursor.execute("""
        INSERT INTO organizations (id, name, slug, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """, (DEFAULT_ORG_ID, "Personal Workspace", "default-workspace", now_iso, now_iso))
        actual_org_id = DEFAULT_ORG_ID
    else:
        actual_org_id = org_row[0]

    cursor.execute("SELECT id FROM users WHERE email = ?", ("owner@editorial.ai",))
    user_row = cursor.fetchone()
    if not user_row:
        print("Seeding default user: owner@editorial.ai...")
        pw_hash = hash_password("admin12345")
        cursor.execute("""
        INSERT INTO users (id, email, hashed_password, full_name, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        """, (DEFAULT_USER_ID, "owner@editorial.ai", pw_hash, "Lead Editor", now_iso, now_iso))
        actual_user_id = DEFAULT_USER_ID
    else:
        actual_user_id = user_row[0]

    cursor.execute("SELECT id FROM organization_memberships WHERE organization_id = ? AND user_id = ?", (actual_org_id, actual_user_id))
    if not cursor.fetchone():
        print("Linking default user to organization with role OWNER...")
        cursor.execute("""
        INSERT INTO organization_memberships (id, organization_id, user_id, role, joined_at)
        VALUES (?, ?, ?, 'OWNER', ?)
        """, (f"mem-{actual_user_id[:8]}-{actual_org_id[:8]}", actual_org_id, actual_user_id, now_iso))

    # 7. Migrate all legacy research_projects to default organization
    cursor.execute("UPDATE research_projects SET organization_id = ? WHERE organization_id IS NULL", (actual_org_id,))
    updated_count = cursor.rowcount
    if updated_count > 0:
        print(f"Migrated {updated_count} legacy research projects to default organization '{actual_org_id}'.")

    conn.commit()
    conn.close()
    print(f"Migration completed successfully for {db_path}.")

if __name__ == "__main__":
    for db in ["editorial.db", "backend/editorial.db"]:
        migrate_database(db)

