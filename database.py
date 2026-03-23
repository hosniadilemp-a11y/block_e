import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

class UnifiedCursor:
    def __init__(self, cursor, is_postgres):
        self.cursor = cursor
        self.is_postgres = is_postgres

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def __iter__(self):
        return iter(self.cursor)

    @property
    def lastrowid(self):
        if self.is_postgres:
            # PostgreSQL doesn't have lastrowid on cursor the same way if multiple inserts happen
            # But for simple cases we might need to handle it via RETURNING
            return None 
        return self.cursor.lastrowid

class UnifiedConnection:
    def __init__(self, conn, is_postgres):
        self.conn = conn
        self.is_postgres = is_postgres

    def execute(self, query, params=None):
        if self.is_postgres:
            query = query.replace('?', '%s')
            cur = self.conn.cursor()
            cur.execute(query, params or ())
            return UnifiedCursor(cur, True)
        else:
            cur = self.conn.execute(query, params or ())
            return UnifiedCursor(cur, False)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def cursor(self):
        if self.is_postgres:
            return self.conn.cursor()
        return self.conn.cursor()

def get_db_connection():
    if DATABASE_URL and DATABASE_URL.startswith('postgres'):
        import psycopg2
        from psycopg2.extras import DictCursor
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
        return UnifiedConnection(conn, True)
    else:
        db_path = os.environ.get('SQLITE_DB', 'database.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return UnifiedConnection(conn, False)
