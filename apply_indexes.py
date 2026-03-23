import os
from database import get_db_connection

def apply_indexes():
    print("Applying indexes to Supabase database...")
    
    if not os.path.exists('indexes.sql'):
        print("Error: indexes.sql not found.")
        return
        
    with open('indexes.sql', 'r') as f:
        sql = f.read()
    
    # Split by semicolon to execute one by one
    commands = [cmd.strip() for cmd in sql.split(';') if cmd.strip()]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    for cmd in commands:
        try:
            print(f"Executing: {cmd[:50]}...")
            cur.execute(cmd)
            conn.commit()
            print("Done.")
        except Exception as e:
            conn.rollback()
            print(f"Error applying index: {e}")
    
    conn.close()
    print("All indexes applied.")

if __name__ == "__main__":
    apply_indexes()
