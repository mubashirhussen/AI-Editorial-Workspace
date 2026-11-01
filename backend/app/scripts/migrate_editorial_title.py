import sqlite3

for db_path in ["editorial.db", "backend/editorial.db"]:
    try:
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(editorial_outputs);").fetchall()]
        if "title" not in cols:
            conn.execute("ALTER TABLE editorial_outputs ADD COLUMN title VARCHAR(255);")
            print(f"Added title to {db_path} editorial_outputs")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error on {db_path}: {e}")

