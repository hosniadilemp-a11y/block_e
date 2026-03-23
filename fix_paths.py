import sqlite3

def fix_db():
    conn = sqlite3.connect('database.db')
    # Replace backslashes with forward slashes in chemin_document
    conn.execute("UPDATE annonces SET chemin_document = REPLACE(chemin_document, '\\', '/') WHERE chemin_document IS NOT NULL")
    conn.commit()
    conn.close()
    print("Paths fixed in DB.")

if __name__ == '__main__':
    fix_db()
