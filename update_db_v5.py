import sqlite3
from werkzeug.security import generate_password_hash

def upgrade_db():
    conn = sqlite3.connect('database.db')
    
    # 1. Add chemin_document to annonces
    try:
        conn.execute("ALTER TABLE annonces ADD COLUMN chemin_document TEXT")
        print("Column chemin_document added to annonces.")
    except sqlite3.OperationalError:
        print("Column chemin_document already exists in annonces.")
        
    # 2. Add / Update exact Resident users
    for i in range(1, 21):
        username = f"apt{i}"
        password = f"2026@{i}"
        hashed_pw = generate_password_hash(password)
        
        user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if user:
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user[0]))
        else:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'resident')", (username, hashed_pw))
            
    # Also update any existing apt username if it was something else, but we'll stick to inserting/updating exact matches.
    
    conn.commit()
    conn.close()
    print("Database upgrade complete.")

if __name__ == '__main__':
    upgrade_db()
