import sqlite3

for db_path in ["editorial.db", "backend/editorial.db"]:
    try:
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(research_briefs);").fetchall()]
        to_add = [
            ("title", "VARCHAR(255) DEFAULT 'Research Brief'"),
            ("key_developments", "JSON DEFAULT '[]'"),
            ("strategic_implications", "JSON DEFAULT '{}'"),
            ("source_references", "JSON DEFAULT '[]'")
        ]
        for col, typ in to_add:
            if col not in cols:
                conn.execute(f"ALTER TABLE research_briefs ADD COLUMN {col} {typ};")
                print(f"Added {col} to {db_path}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error on {db_path}: {e}")

