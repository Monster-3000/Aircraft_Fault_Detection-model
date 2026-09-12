import sqlite3
import hashlib
import os

DB_PATH = "users.db"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    """)
    
    # Check if default admin exists
    cursor.execute("SELECT * FROM users WHERE username = ?", ("akash",))
    admin_exists = cursor.fetchone()
    
    if not admin_exists:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("akash", hash_password("akash"), "Admin")
        )
    
    conn.commit()
    conn.close()

# Initialize DB when this module is imported
init_db()
