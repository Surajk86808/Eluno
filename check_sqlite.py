import sqlite3
import os

db_path = 'backend/order_management.db'
if not os.path.exists(db_path):
    print(f"{db_path} does not exist")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('--- SQLite Table Counts ---')
    for (table_name,) in tables:
        if table_name == 'sqlite_sequence': continue
        cursor.execute(f"SELECT count(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Table '{table_name}': {count} rows")
    conn.close()
