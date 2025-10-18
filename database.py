import psycopg2
import asyncio
from typing import List, Dict, Any, Optional

DB_CONFIG = {
    "dbname": "hotels",
    "user": "postgres",
    "password": "8691",
    "host": "localhost",
    "port": 5432
}

# -------------------- Connection --------------------
def get_connection():
    """Return a synchronous PostgreSQL connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print("Database connection error:", e)
        raise

# -------------------- Synchronous Functions --------------------
def select_row(table: str, columns="*", condition: Optional[str] = None, params: Optional[list] = None) -> List[dict]:
    """Select rows and return list of dicts"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        if isinstance(columns, (list, tuple)):
            columns_str = ', '.join(columns)
        else:
            columns_str = columns
        sql = f"SELECT {columns_str} FROM {table}"
        if condition:
            sql += f" WHERE {condition}"
        cur.execute(sql, params or [])
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        result = [dict(zip(colnames, row)) for row in rows]
        cur.close()
        conn.close()
        return result
    except Exception as e:
        print("Database error in select_row:", e)
        raise

def read_rows(table: str, columns="*", condition: Optional[str] = None, params: Optional[list] = None) -> List[tuple]:
    """Select rows and return raw tuples"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        if isinstance(columns, (list, tuple)):
            columns_str = ', '.join(columns)
        else:
            columns_str = columns
        sql = f"SELECT {columns_str} FROM {table}"
        if condition:
            sql += f" WHERE {condition}"
        cur.execute(sql, params or [])
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print("Database error in read_rows:", e)
        raise

def insert_row(table: str, data: dict) -> int:
    """Insert a row and return its ID"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        cur.execute(sql, list(data.values()))
        inserted_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return inserted_id
    except Exception as e:
        print("Database error in insert_row:", e)
        raise

def update_row(table: str, updates: dict, condition: str, params: Optional[list] = None):
    """Update rows"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        set_clause = ', '.join([f"{col} = %s" for col in updates.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        cur.execute(sql, list(updates.values()) + (params or []))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Database error in update_row:", e)
        raise

def delete_row(table: str, condition: str, params: Optional[list] = None):
    """Delete rows"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        sql = f"DELETE FROM {table} WHERE {condition}"
        cur.execute(sql, params or [])
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Database error in delete_row:", e)
        raise

# -------------------- Async Wrappers --------------------
async def select_row_async(table: str, columns="*", condition: Optional[str] = None, params: Optional[list] = None) -> List[dict]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, select_row, table, columns, condition, params)

async def read_rows_async(table: str, columns="*", condition: Optional[str] = None, params: Optional[list] = None) -> List[tuple]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, read_rows, table, columns, condition, params)

async def insert_row_async(table: str, data: dict) -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, insert_row, table, data)

async def update_row_async(table: str, updates: dict, condition: str, params: Optional[list] = None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, update_row, table, updates, condition, params)

async def delete_row_async(table: str, condition: str, params: Optional[list] = None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, delete_row, table, condition, params)
