import sqlite3

def migrate():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    try:
        # Add user_id to annonces
        cur.execute("ALTER TABLE annonces ADD COLUMN user_id INTEGER REFERENCES users(id)")
        cur.execute("UPDATE annonces SET user_id = 52")
        print("Annonces table migrated.")
    except Exception as e:
        print("Error migrating annonces (maybe already done):", e)
        
    try:
        # Recreate depenses table
        cur.execute('''
        CREATE TABLE depenses_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            montant REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            categorie TEXT NOT NULL,
            user_id INTEGER REFERENCES users(id),
            soldeApres REAL NOT NULL,
            document TEXT
        )
        ''')
        cur.execute('''
        INSERT INTO depenses_new (id, description, montant, date, categorie, soldeApres, document, user_id)
        SELECT id, description, montant, date, categorie, soldeApres, document, 52 FROM depenses
        ''')
        cur.execute("DROP TABLE depenses")
        cur.execute("ALTER TABLE depenses_new RENAME TO depenses")
        print("Depenses table migrated.")
    except Exception as e:
        print("Error migrating depenses (maybe already done):", e)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()
