import os
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_phase25")

TABLE_DEFS = [
    """
    CREATE TABLE IF NOT EXISTS research_entities (
        id VARCHAR(36) PRIMARY KEY,
        project_id VARCHAR(36) NOT NULL,
        name VARCHAR(255) NOT NULL,
        normalized_name VARCHAR(255) NOT NULL,
        entity_type VARCHAR(50) NOT NULL,
        source_id VARCHAR(36),
        supporting_excerpt TEXT,
        confidence FLOAT NOT NULL DEFAULT 0.9,
        extraction_method VARCHAR(50) NOT NULL DEFAULT 'heuristic_nlp',
        created_at DATETIME NOT NULL,
        FOREIGN KEY (project_id) REFERENCES research_projects(id) ON DELETE CASCADE,
        FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_entities_project_type ON research_entities (project_id, entity_type);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_entities_normalized ON research_entities (normalized_name);
    """,
    """
    CREATE TABLE IF NOT EXISTS research_claims (
        id VARCHAR(36) PRIMARY KEY,
        project_id VARCHAR(36) NOT NULL,
        source_id VARCHAR(36) NOT NULL,
        claim_text TEXT NOT NULL,
        supporting_excerpt TEXT NOT NULL,
        evidence_classification VARCHAR(50) NOT NULL DEFAULT 'DIRECTLY_STATED',
        entity_references JSON NOT NULL,
        confidence FLOAT NOT NULL DEFAULT 0.9,
        publication_date VARCHAR(100),
        created_at DATETIME NOT NULL,
        FOREIGN KEY (project_id) REFERENCES research_projects(id) ON DELETE CASCADE,
        FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_claims_project_classification ON research_claims (project_id, evidence_classification);
    """,
    """
    CREATE TABLE IF NOT EXISTS research_relationships (
        id VARCHAR(36) PRIMARY KEY,
        project_id VARCHAR(36) NOT NULL,
        source_entity_name VARCHAR(255) NOT NULL,
        target_entity_name VARCHAR(255) NOT NULL,
        relationship_type VARCHAR(50) NOT NULL,
        source_id VARCHAR(36),
        supporting_evidence TEXT NOT NULL,
        confidence FLOAT NOT NULL DEFAULT 0.85,
        explanation TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (project_id) REFERENCES research_projects(id) ON DELETE CASCADE,
        FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_relationships_project_type ON research_relationships (project_id, relationship_type);
    """,
    """
    CREATE TABLE IF NOT EXISTS research_contradictions (
        id VARCHAR(36) PRIMARY KEY,
        project_id VARCHAR(36) NOT NULL,
        claim_a_id VARCHAR(36),
        claim_b_id VARCHAR(36),
        source_a_id VARCHAR(36),
        source_b_id VARCHAR(36),
        claim_a_text TEXT NOT NULL,
        claim_b_text TEXT NOT NULL,
        disagreement_nature TEXT NOT NULL,
        possible_explanations TEXT NOT NULL,
        unresolved_questions TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (project_id) REFERENCES research_projects(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_contradictions_project ON research_contradictions (project_id);
    """,
    """
    CREATE TABLE IF NOT EXISTS research_trends (
        id VARCHAR(36) PRIMARY KEY,
        project_id VARCHAR(36) NOT NULL,
        theme VARCHAR(255) NOT NULL,
        category VARCHAR(50) NOT NULL,
        supporting_source_ids JSON NOT NULL,
        evidence_summary TEXT NOT NULL,
        is_prediction BOOLEAN NOT NULL DEFAULT 0,
        confidence FLOAT NOT NULL DEFAULT 0.85,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (project_id) REFERENCES research_projects(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_trends_project_cat ON research_trends (project_id, category);
    """
]

def migrate_db(db_path: str):
    if not os.path.exists(db_path):
        logger.info(f"DB not found at {db_path}, skipping.")
        return
    
    logger.info(f"Migrating {db_path} for Phase 25...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    for stmt in TABLE_DEFS:
        cur.execute(stmt)
        
    conn.commit()
    conn.close()
    logger.info(f"Phase 25 migration completed for {db_path}.")

if __name__ == "__main__":
    for p in ["editorial.db", "backend/editorial.db"]:
        migrate_db(p)

