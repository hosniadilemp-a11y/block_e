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
    
    # Tables à migrer
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
    
    bool_columns = {
        'polls': ['is_active']
    }
    
    try:
        pg_cur.execute("SET session_replication_role = 'replica';")
        
        for table in tables:
            print(f"Migration de la table {table}...")
            
            # Récupérer les colonnes de la table cible (Postgres) - Spécifier le Schéma 'public'
            pg_cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND table_schema = 'public'")
            pg_cols = [row[0] for row in pg_cur.fetchall()]
            
            if not pg_cols:
                # Essayer en minuscule au cas où
                pg_cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table.lower()}' AND table_schema = 'public'")
                pg_cols = [row[0] for row in pg_cur.fetchall()]
            
            if not pg_cols:
                print(f"Attention: Table {table} non trouvée dans Postgres.")
                continue

            # Récupérer les données de la source (SQLite)
            sl_cur.execute(f"SELECT * FROM {table} LIMIT 1")
            sample = sl_cur.fetchone()
            if sample is None:
                print(f"Table {table} vide, passage.")
                continue
            
            sl_cols_available = sample.keys()
            # Intersection Unique
            common_cols = []
            for c in pg_cols:
                if c in sl_cols_available and c not in common_cols:
                    common_cols.append(c)
            
            col_list = ", ".join(common_cols)
            placeholders = ", ".join(["%s"] * len(common_cols))
            
            pg_cur.execute(f"TRUNCATE TABLE {table} CASCADE")
            
            sl_cur.execute(f"SELECT * FROM {table}")
            rows = sl_cur.fetchall()
            for row in rows:
                val_list = []
                for col in common_cols:
                    val = row[col]
                    if table in bool_columns and col in bool_columns[table]:
                        val = bool(val) if val is not None else None
                    val_list.append(val)
                    
                pg_cur.execute(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})", tuple(val_list))
                
            # Reset sequence
            try:
                pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}")
            except:
                pass
        
        pg_cur.execute("SET session_replication_role = 'origin';")
        pg_conn.commit()
        print("Migration terminée avec succès !")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"Erreur lors de la migration: {e}")
    finally:
        sl_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
