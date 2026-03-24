"""V22 PostgreSQL migration: Add `paye` column to depenses."""
from dotenv import load_dotenv
load_dotenv()
import os, psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("No DATABASE_URL found in .env or environment. Skipping Postgres migration.")
else:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE depenses ADD COLUMN paye BOOLEAN DEFAULT TRUE;")
        cur.execute("UPDATE depenses SET paye = TRUE WHERE paye IS NULL;")
        conn.commit()
        print("PostgreSQL V22: 'paye' column added and all existing set to TRUE.")
    except Exception as e:
        print("Error (maybe already done):", e)
        conn.rollback()
    cur.close()
    conn.close()
