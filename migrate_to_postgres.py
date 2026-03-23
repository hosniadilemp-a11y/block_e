import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB = 'database.db'
POSTGRES_URL = os.environ.get('DATABASE_URL')

def migrate():
    if not POSTGRES_URL:
        print("Erreur: DATABASE_URL non définie dans l'environnement.")
        return

    print(f"Migration de {SQLITE_DB} vers PostgreSQL...")
    
    sl_conn = sqlite3.connect(SQLITE_DB)
    sl_conn.row_factory = sqlite3.Row
    sl_cur = sl_conn.cursor()
    
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cur = pg_conn.cursor()
    
    # Tables à migrer dans l'ordre (respect des FK)
    tables = [
        'users',
        'polls',
        'poll_options',
        'votes',
        'annonces',
        'depenses',
        'cotisations',
        'documents',
        'suggestions',
        'suggestions_votes',
        'logs'
    ]
    
    for table in tables:
        print(f"Migration de la table {table}...")
        sl_cur.execute(f"SELECT * FROM {table}")
        rows = sl_cur.fetchall()
        
        if not rows:
            print(f"Table {table} vide, passage.")
            continue
            
        columns = rows[0].keys()
        
        # In SQLite, some tables might have columns that are slightly different
        # but we assume schema_postgres.sql matched the V7 fusion.
        
        col_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        
        # Truncate before insert (optional, safer)
        pg_cur.execute(f"TRUNCATE TABLE {table} CASCADE")
        
        for row in rows:
            pg_cur.execute(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})", tuple(row))
            
        # Reset sequence for SERIAL
        pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}")
        
    pg_conn.commit()
    sl_conn.close()
    pg_conn.close()
    print("Migration terminée avec succès !")

if __name__ == "__main__":
    migrate()
