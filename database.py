import os
import sqlite3
import re
import datetime as dt
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')


class RowProxy:
    """Row wrapper supporting both row['col'] and row[0] indexing — like sqlite3.Row."""
    def __init__(self, data: dict):
        self._data = data
        self._keys = list(data.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[self._keys[key]]
        return self._data[key]

    def keys(self):
        return self._keys

    def get(self, key, default=None):
        return self._data.get(key, default)

    def items(self):
        return self._data.items()

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return repr(self._data)


class UnifiedCursor:
    def __init__(self, cursor, is_postgres):
        self.cursor = cursor
        self.is_postgres = is_postgres
        self._last_id = None

    def execute(self, query, params=None):
        if self.is_postgres:
            # 1. Translate SQLite strftime -> PostgreSQL TO_CHAR
            query = re.sub(r"strftime\(['\"]%Y['\"],\s*([^)]+)\)", r"TO_CHAR(\1, 'YYYY')", query, flags=re.IGNORECASE)
            query = re.sub(r"strftime\(['\"]%m['\"],\s*([^)]+)\)", r"TO_CHAR(\1, 'MM')", query, flags=re.IGNORECASE)

            # 2. Boolean: is_active = 1 -> is_active = TRUE
            query = re.sub(r'\b(is_active)\s*=\s*1\b', r'\1 = TRUE', query, flags=re.IGNORECASE)
            query = re.sub(r'\b(is_active)\s*=\s*0\b', r'\1 = FALSE', query, flags=re.IGNORECASE)
            query = re.sub(r'SET\s+(is_active)\s*=\s*1\b', r'SET \1 = TRUE', query, flags=re.IGNORECASE)
            query = re.sub(r'SET\s+(is_active)\s*=\s*0\b', r'SET \1 = FALSE', query, flags=re.IGNORECASE)

            # 3. Auto RETURNING id for INSERT
            is_insert = query.strip().upper().startswith('INSERT')
            if is_insert and 'RETURNING' not in query.upper():
                query += " RETURNING id"

            # 4. Placeholders: ? -> %s, escape remaining %
            query = query.replace('?', '%s')
            query = query.replace('%', '%%').replace('%%s', '%s')

            self.cursor.execute(query, params or ())

            if is_insert:
                try:
                    res = self.cursor.fetchone()
                    if res:
                        self._last_id = res[0]
                except Exception:
                    pass
            return self
        else:
            self.cursor.execute(query, params or ())
            return self

    def _convert_row(self, row):
        """Convert PostgreSQL DictRow datetime fields to strings and wrap in RowProxy."""
        if row is None:
            return None
        if self.is_postgres:
            converted = {}
            for k in row.keys():
                v = row[k]
                if isinstance(v, (dt.datetime, dt.date)):
                    v = str(v)
                converted[k] = v
            return RowProxy(converted)
        return row

    def fetchone(self):
        return self._convert_row(self.cursor.fetchone())

    def fetchall(self):
        return [self._convert_row(r) for r in self.cursor.fetchall()]

    def __iter__(self):
        for row in self.cursor:
            yield self._convert_row(row)

    @property
    def lastrowid(self):
        if self.is_postgres:
            return self._last_id
        return getattr(self.cursor, 'lastrowid', None)

    def __getitem__(self, index):
        return self.cursor[index]

    def close(self):
        self.cursor.close()


class UnifiedConnection:
    def __init__(self, conn, is_postgres):
        self.conn = conn
        self.is_postgres = is_postgres

    def execute(self, query, params=None):
        cur = self.cursor()
        return cur.execute(query, params)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def cursor(self):
        if self.is_postgres:
            return UnifiedCursor(self.conn.cursor(), True)
        else:
            return UnifiedCursor(self.conn.cursor(), False)


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
