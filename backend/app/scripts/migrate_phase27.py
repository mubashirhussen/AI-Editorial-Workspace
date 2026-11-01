import os
import sqlite3
import logging
import uuid
from datetime import datetime, timezone
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_phase27")

def migrate_db(db_path: str):
    if not os.path.exists(db_path):
        logger.info(f"DB not found at {db_path}, skipping.")
        return

    logger.info(f"Migrating {db_path} for Phase 27...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Create editorial_versions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS editorial_versions (
        id VARCHAR(36) PRIMARY KEY,
        organization_id VARCHAR(36),
        document_type VARCHAR(50) NOT NULL,
        document_id VARCHAR(36) NOT NULL,
        version_number INTEGER NOT NULL,
        title VARCHAR(255),
        content_snapshot TEXT NOT NULL,
        change_summary TEXT NOT NULL DEFAULT '',
        change_type VARCHAR(50) NOT NULL DEFAULT 'MANUAL_EDIT',
        created_by VARCHAR(36),
        created_at DATETIME NOT NULL,
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_editorial_versions_doc 
    ON editorial_versions (document_type, document_id, version_number);
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_editorial_versions_created 
    ON editorial_versions (document_id, created_at);
    """)

    now_str = datetime.now(timezone.utc).isoformat()

    # 2. Backfill initial snapshots for existing WritingDrafts
    cur.execute("SELECT id, project_id, title, original_content, revised_content, created_at FROM writing_drafts;")
    drafts = cur.fetchall()
    for draft_id, project_id, title, orig_c, rev_c, created_at in drafts:
        cur.execute("""
            SELECT COUNT(*) FROM editorial_versions 
            WHERE document_type = 'WRITING_DRAFT' AND document_id = ?;
        """, (draft_id,))
        if cur.fetchone()[0] == 0:
            content = rev_c or orig_c or ""
            # Find organization_id from project if possible
            org_id = None
            if project_id:
                cur.execute("SELECT organization_id FROM research_projects WHERE id = ?", (project_id,))
                row = cur.fetchone()
                if row:
                    org_id = row[0]

            cur.execute("""
                INSERT INTO editorial_versions (
                    id, organization_id, document_type, document_id, version_number,
                    title, content_snapshot, change_summary, change_type, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()), org_id, 'WRITING_DRAFT', draft_id, 1,
                title or "Editorial Draft", content, "Initial document snapshot",
                "INITIAL", None, created_at or now_str
            ))
            logger.info(f"Created initial version for draft {draft_id}")

    # 3. Backfill initial snapshots for existing EditorialOutputs
    cur.execute("SELECT id, project_id, headline, content, created_at FROM editorial_outputs;")
    editorials = cur.fetchall()
    for ed_id, project_id, headline, content, created_at in editorials:
        cur.execute("""
            SELECT COUNT(*) FROM editorial_versions 
            WHERE document_type = 'EDITORIAL_OUTPUT' AND document_id = ?;
        """, (ed_id,))
        if cur.fetchone()[0] == 0:
            org_id = None
            if project_id:
                cur.execute("SELECT organization_id FROM research_projects WHERE id = ?", (project_id,))
                row = cur.fetchone()
                if row:
                    org_id = row[0]

            cur.execute("""
                INSERT INTO editorial_versions (
                    id, organization_id, document_type, document_id, version_number,
                    title, content_snapshot, change_summary, change_type, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()), org_id, 'EDITORIAL_OUTPUT', ed_id, 1,
                headline or "Newsletter Article", content or "", "Initial editorial output",
                "INITIAL", None, created_at or now_str
            ))
            logger.info(f"Created initial version for editorial output {ed_id}")

    # 4. Backfill initial snapshots for existing ResearchBriefs
    cur.execute("SELECT id, project_id, title, executive_summary, created_at FROM research_briefs;")
    briefs = cur.fetchall()
    for brief_id, project_id, title, exec_sum, created_at in briefs:
        cur.execute("""
            SELECT COUNT(*) FROM editorial_versions 
            WHERE document_type = 'RESEARCH_BRIEF' AND document_id = ?;
        """, (brief_id,))
        if cur.fetchone()[0] == 0:
            org_id = None
            if project_id:
                cur.execute("SELECT organization_id FROM research_projects WHERE id = ?", (project_id,))
                row = cur.fetchone()
                if row:
                    org_id = row[0]

            cur.execute("""
                INSERT INTO editorial_versions (
                    id, organization_id, document_type, document_id, version_number,
                    title, content_snapshot, change_summary, change_type, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()), org_id, 'RESEARCH_BRIEF', brief_id, 1,
                title or "Research Synthesis Brief", exec_sum or "", "Initial research brief",
                "INITIAL", None, created_at or now_str
            ))
            logger.info(f"Created initial version for research brief {brief_id}")

    conn.commit()
    conn.close()
    logger.info(f"Migration completed successfully for {db_path}!")

if __name__ == "__main__":
    db_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "editorial.db"),
        os.path.join(os.path.dirname(__file__), "..", "..", "editorial.db"),
    ]
    for p in db_paths:
        abs_p = os.path.abspath(p)
        migrate_db(abs_p)
