import sqlite3
import os

def migrate():
    print("Demarrage de la migration V7...")
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Expand `users` table
    try:
        c.execute("ALTER TABLE users ADD COLUMN appartement_numero INTEGER")
        c.execute("ALTER TABLE users ADD COLUMN nom_complet TEXT")
        c.execute("ALTER TABLE users ADD COLUMN telephone TEXT DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN statut TEXT DEFAULT 'inconnu'")
    except sqlite3.OperationalError as e:
        print("Colonnes deja presentes:", e)

    print("Recuperation des appartements existants...")
    appts = c.execute("SELECT * FROM appartements").fetchall()
    
    mapping_appt_user = {}

    for a in appts:
        u = c.execute("SELECT id FROM users WHERE username = ?", (f"apt{a['numero']}",)).fetchone()
        if u:
            c.execute("UPDATE users SET appartement_numero=?, nom_complet=?, statut=? WHERE id=?", 
                      (a['numero'], a['resident'], a['statut'], u['id']))
            mapping_appt_user[a['id']] = u['id']
            print(f"Mise a jour locataire ID {u['id']} avec {a['resident']}")
        else:
            print(f"ATTENTION: Aucun user trouve pour apt{a['numero']}")

    print("Migration table Cotisations vers User_ID...")
    c.execute("""
    CREATE TABLE IF NOT EXISTS cotisations_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        montant REAL NOT NULL,
        annee INTEGER NOT NULL DEFAULT 2025,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    old_cots = c.execute("SELECT * FROM cotisations").fetchall()
    insertions = 0
    for cot in old_cots:
        u_id = mapping_appt_user.get(cot['appartement_id'])
        if u_id:
            c.execute("INSERT INTO cotisations_new (id, user_id, montant, annee, date) VALUES (?, ?, ?, ?, ?)",
                      (cot['id'], u_id, cot['montant'], cot['annee'], cot['date']))
            insertions += 1
    print(f"{insertions} Cotisations migrees.")
    
    c.execute("DROP TABLE cotisations")
    c.execute("ALTER TABLE cotisations_new RENAME TO cotisations")

    try:
        c.execute("ALTER TABLE depenses ADD COLUMN user_id INTEGER REFERENCES users(id)")
    except sqlite3.OperationalError:
        pass

    c.execute("DROP TABLE appartements")

    conn.commit()
    conn.close()
    print("Migration V7 terminee avec succes.")

if __name__ == '__main__':
    migrate()
