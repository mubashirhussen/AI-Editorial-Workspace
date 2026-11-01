import sqlite3

for db_path in ["editorial.db", "backend/editorial.db"]:
    try:
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(source_analyses);").fetchall()]
        to_add = [
            ("summary", "TEXT"),
            ("key_points", "JSON DEFAULT '[]'"),
            ("reported_facts", "JSON DEFAULT '[]'"),
            ("founder_implications", "JSON DEFAULT '{}'"),
            ("uncertainties", "JSON DEFAULT '[]'"),
            ("newsletter_angles", "JSON DEFAULT '[]'")
        ]
        for col, typ in to_add:
            if col not in cols:
                conn.execute(f"ALTER TABLE source_analyses ADD COLUMN {col} {typ};")
                print(f"Added {col} to {db_path} source_analyses")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error on {db_path}: {e}")

