import sqlite3

for db_path in ["editorial.db", "backend/editorial.db"]:
    try:
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(sources);").fetchall()]
        to_add = [
            ("original_url", "VARCHAR(1024)"),
            ("raw_content", "TEXT")
        ]
        for col, typ in to_add:
            if col not in cols:
                conn.execute(f"ALTER TABLE sources ADD COLUMN {col} {typ};")
                print(f"Added {col} to {db_path} sources")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error on {db_path}: {e}")

