import sqlite3

for db_path in ["editorial.db", "backend/editorial.db"]:
    try:
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(writing_drafts);").fetchall()]
        to_add = [
            ("word_count", "INTEGER DEFAULT 0"),
            ("readability_score", "FLOAT DEFAULT 0.0")
        ]
        for col, typ in to_add:
            if col not in cols:
                conn.execute(f"ALTER TABLE writing_drafts ADD COLUMN {col} {typ};")
                print(f"Added {col} to {db_path} writing_drafts")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error on {db_path}: {e}")

