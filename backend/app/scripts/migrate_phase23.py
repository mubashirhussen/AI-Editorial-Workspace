import sqlite3
import os
import sys

# Ensure backend in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
workspace_root = os.path.dirname(backend_dir)
for p in [workspace_root, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

for db_name in ["editorial.db", "backend/editorial.db"]:
    if os.path.exists(db_name):
        conn = sqlite3.connect(db_name)
        cols = [c[1] for c in conn.execute("PRAGMA table_info(editorial_outputs)").fetchall()]
        if "original_content" not in cols:
            conn.execute("ALTER TABLE editorial_outputs ADD COLUMN original_content TEXT")
        if "version" not in cols:
            conn.execute("ALTER TABLE editorial_outputs ADD COLUMN version INTEGER DEFAULT 1")
        if "ai_review_results" not in cols:
            conn.execute("ALTER TABLE editorial_outputs ADD COLUMN ai_review_results JSON DEFAULT '{}'")
        conn.commit()
        conn.close()
        print(f"Migrated {db_name}")

from backend.app.core.database import engine, Base
import backend.app.models.base
Base.metadata.create_all(bind=engine)
print("Phase 23 DB migration completed successfully.")

