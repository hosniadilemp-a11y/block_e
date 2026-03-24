import os
from app import get_db_connection

def migrate_postgres():
    conn = get_db_connection()
    # In psycopg2, conn is a connection object and we need a cursor.
    # But get_db_connection() might return a psycopg2 connection or sqlite3 connection.
    # In app.py: conn = psycopg2.connect(...)
    cur = conn.cursor()
    
    try:
        # Add user_id to annonces
        cur.execute("ALTER TABLE annonces ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;")
        cur.execute("UPDATE annonces SET user_id = 52;")
        print("Annonces table migrated in PostgreSQL.")
    except Exception as e:
        print("Error migrating annonces:", e)
        conn.rollback() # Important for Postgres transaction
        
    try:
        # Depenses has payePar TEXT, let's drop it and add user_id
        # Note: Postgres allows dropping columns
        cur.execute("ALTER TABLE depenses DROP COLUMN IF EXISTS payepar;")
        cur.execute("ALTER TABLE depenses ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;")
        cur.execute("UPDATE depenses SET user_id = 52;")
        print("Depenses table migrated in PostgreSQL.")
    except Exception as e:
        print("Error migrating depenses:", e)
        conn.rollback()

    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    migrate_postgres()
