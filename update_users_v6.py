import sqlite3
from werkzeug.security import generate_password_hash

def upgrade_users():
    conn = sqlite3.connect('database.db')
    
    # 1. Delete all non-admin users
    conn.execute("DELETE FROM users WHERE role != 'admin'")
    
    # 2. Update appartements to 81-100
    appts = conn.execute("SELECT id FROM appartements ORDER BY id ASC").fetchall()
    
    new_num = 81
    for a in appts:
        conn.execute("UPDATE appartements SET numero = ? WHERE id = ?", (str(new_num), a[0]))
        # Create corresponding user
        username = f"apt{new_num}"
        password = f"2026@{new_num}"
        hashed_pw = generate_password_hash(password)
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'resident')", (username, hashed_pw))
        
        new_num += 1
        
    conn.commit()
    conn.close()
    print("Users cleared and recreated from apt81 to apt100. Appartements table updated.")

if __name__ == '__main__':
    upgrade_users()
