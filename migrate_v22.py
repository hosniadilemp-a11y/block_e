"""
V22 Migration: Add `paye` (paid) column to depenses table.
Also migrates SQLite database if used.
"""
import os, sys

# Try PostgreSQL first
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE depenses ADD COLUMN paye BOOLEAN DEFAULT TRUE;")
        cur.execute("UPDATE depenses SET paye = TRUE WHERE paye IS NULL;")
        conn.commit()
        print("PostgreSQL: 'paye' column added to depenses.")
    except Exception as e:
        print("PostgreSQL error (maybe already done):", e)
        conn.rollback()
    cur.close()
    conn.close()
else:
    # SQLite fallback
    import sqlite3
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE depenses ADD COLUMN paye INTEGER DEFAULT 1;")
        cur.execute("UPDATE depenses SET paye = 1 WHERE paye IS NULL;")
        conn.commit()
        print("SQLite: 'paye' column added to depenses.")
    except Exception as e:
        print("SQLite error (maybe already done):", e)
    conn.close()

print("Migration V22 done.")
