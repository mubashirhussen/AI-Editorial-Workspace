import os
import sqlite3
import logging
from datetime import datetime, timezone
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_phase26")

def migrate_db(db_path: str):
    if not os.path.exists(db_path):
        logger.info(f"DB not found at {db_path}, skipping.")
        return

    logger.info(f"Migrating {db_path} for Phase 26...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Create editorial_style_profiles table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS editorial_style_profiles (
        id VARCHAR(36) PRIMARY KEY,
        organization_id VARCHAR(36),
        name VARCHAR(255) NOT NULL,
        publication_name VARCHAR(255) NOT NULL DEFAULT 'This Week in AI',
        tone VARCHAR(100) NOT NULL DEFAULT 'Authoritative, analytical, objective',
        target_audience VARCHAR(255) NOT NULL DEFAULT 'Founders, builders, and operators',
        max_sentence_length INTEGER NOT NULL DEFAULT 25,
        preferred_sentence_length INTEGER NOT NULL DEFAULT 18,
        max_paragraph_length INTEGER NOT NULL DEFAULT 75,
        target_flesch_score FLOAT NOT NULL DEFAULT 65.0,
        preferred_terminology JSON NOT NULL,
        words_to_avoid JSON NOT NULL,
        headline_style VARCHAR(100) NOT NULL DEFAULT 'Direct, analytical, hook-driven',
        formatting_preferences JSON NOT NULL,
        is_default BOOLEAN NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_style_org_default ON editorial_style_profiles (organization_id, is_default);
    """)

    # 2. Add columns to writing_drafts if they don't exist
    cur.execute("PRAGMA table_info(writing_drafts);")
    cols = [row[1] for row in cur.fetchall()]
    if "style_profile_id" not in cols:
        cur.execute("ALTER TABLE writing_drafts ADD COLUMN style_profile_id VARCHAR(36);")
        logger.info("Added column style_profile_id to writing_drafts")
    if "style_score" not in cols:
        cur.execute("ALTER TABLE writing_drafts ADD COLUMN style_score FLOAT;")
        logger.info("Added column style_score to writing_drafts")

    # 3. Seed default style profile if none exists
    cur.execute("SELECT COUNT(*) FROM editorial_style_profiles;")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        now_str = datetime.now(timezone.utc).isoformat()
        preferred_terms = json.dumps({
            "AI chip": "AI accelerator",
            "running the model": "inference",
            "hallucination": "model fabrication",
            "smart agent": "autonomous agent",
            "super intelligence": "AGI",
            "large model": "frontier model"
        })
        words_avoid = json.dumps([
            "game-changer",
            "delve",
            "revolutionary",
            "skyrocketed",
            "pivotal",
            "synergistic",
            "paradigm shift",
            "unrivaled",
            "best-in-class",
            "tapestry",
            "unprecedented miracle",
            "mind-blowing"
        ])
        formatting_pref = json.dumps({
            "oxford_comma": True,
            "inline_citations": True,
            "bullet_points_allowed": True,
            "markdown_headings": True
        })

        cur.execute("""
        INSERT INTO editorial_style_profiles (
            id, organization_id, name, publication_name, tone, target_audience,
            max_sentence_length, preferred_sentence_length, max_paragraph_length,
            target_flesch_score, preferred_terminology, words_to_avoid, headline_style,
            formatting_preferences, is_default, created_at, updated_at
        ) VALUES (
            'default-style-profile-uuid-00000',
            NULL,
            'This Week in AI Standard',
            'This Week in AI',
            'Authoritative, analytical, objective',
            'Founders, builders, and operators',
            25,
            18,
            75,
            65.0,
            ?,
            ?,
            'Direct, analytical, hook-driven',
            ?,
            1,
            ?,
            ?
        );
        """, (preferred_terms, words_avoid, formatting_pref, now_str, now_str))
        logger.info("Seeded default style profile 'This Week in AI Standard'.")

    conn.commit()
    conn.close()
    logger.info(f"Phase 26 migration completed for {db_path}.")

if __name__ == "__main__":
    for p in ["editorial.db", "backend/editorial.db"]:
        migrate_db(p)

