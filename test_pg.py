import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn_string = os.environ.get('DATABASE_URL')
if conn_string:
    conn_string = conn_string.strip()

print(f"Tentative de connexion à {conn_string.split('@')[1]}...")

try:
    conn = psycopg2.connect(conn_string)
    print("Connexion réussie !")
    cur = conn.cursor()
    
    with open('schema_postgres.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
        print("Initialisation du schéma...")
        cur.execute(sql)
        conn.commit()
        print("Schéma initialisé avec succès.")
        
    conn.close()
except Exception as e:
    print(f"Erreur: {e}")
