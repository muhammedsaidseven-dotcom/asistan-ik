import sqlite3
import os
import datetime
import hashlib

DB_PATH = "hr_records.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT,
            details TEXT,
            status TEXT,
            file_number TEXT,
            created_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            status TEXT,
            created_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    try:
        c.execute('ALTER TABLE records ADD COLUMN state_json TEXT')
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            print(f"FATAL ERROR ADDING COLUMN: {e}")
            import streamlit as st
            st.error(f"Veritabanı Güncelleme Hatası: {e}")

    conn.commit()
    conn.close()
    
    # Initialize default admin if not exists
    create_default_admin()

def log_action(username, action):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute('INSERT INTO logs (username, action, created_at) VALUES (?, ?, ?)', (username, action, now))
    conn.commit()
    conn.close()

def get_logs(limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM logs ORDER BY id DESC LIMIT ?', (limit,))
    logs = c.fetchall()
    conn.close()
    return [dict(row) for row in logs]

def get_approved_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT id, username, role, created_at FROM users WHERE status = "approved" AND username != "admin" ORDER BY id DESC')
    users = c.fetchall()
    conn.close()
    return [dict(row) for row in users]

def create_record(employee_name, details, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Generate a simple file number like Dosya 2026-0001
    c.execute('SELECT COUNT(*) FROM records')
    count = c.fetchone()[0]
    file_number = f"Dosya {datetime.datetime.now().year}-{(count + 1):04d}"
    
    now = datetime.datetime.now().isoformat()
    c.execute('''
        INSERT INTO records (employee_name, details, status, file_number, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (employee_name, details, status, file_number, now))
    
    record_id = c.lastrowid
    conn.commit()
    conn.close()
    return record_id

def update_status(record_id, status):
    if not record_id:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE records SET status = ? WHERE id = ?', (status, record_id))
    conn.commit()
    conn.close()

def update_state(record_id, state_json_str):
    if not record_id:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE records SET state_json = ? WHERE id = ?', (state_json_str, record_id))
    conn.commit()
    conn.close()

def get_all_records():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM records ORDER BY id DESC')
    records = c.fetchall()
    conn.close()
    return [dict(row) for row in records]

def get_summary_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM records')
    total = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM records WHERE status = "Tutanak Tutuldu"')
    tutanak = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM records WHERE status = "Savunma Bekleniyor"')
    bekleyen = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM records WHERE status = "Savunma Alındı"')
    alindi = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM records WHERE status LIKE "Sonuçlandı%"')
    sonuc = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total,
        "tutanak": tutanak,
        "bekleyen": bekleyen,
        "alindi": alindi,
        "sonuc": sonuc
    }

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def change_password(username, new_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pwd_hash = hash_password(new_password)
    c.execute('UPDATE users SET password_hash = ? WHERE username = ?', (pwd_hash, username))
    conn.commit()
    conn.close()

def create_default_admin():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = "admin"')
    if not c.fetchone():
        now = datetime.datetime.now().isoformat()
        pwd_hash = hash_password("admin123")
        c.execute('''
            INSERT INTO users (username, password_hash, role, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', ("admin", pwd_hash, "admin", "approved", now))
        conn.commit()
    conn.close()

def create_user(username, password, role="user", status="pending"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        now = datetime.datetime.now().isoformat()
        pwd_hash = hash_password(password)
        c.execute('''
            INSERT INTO users (username, password_hash, role, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, pwd_hash, role, status, now))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username already exists
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password_hash, role, status FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    
    if row:
        stored_hash, role, status = row
        if stored_hash == hash_password(password):
            return {"role": role, "status": status}
    return None

def get_pending_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT id, username, created_at FROM users WHERE status = "pending" ORDER BY id DESC')
    users = c.fetchall()
    conn.close()
    return [dict(row) for row in users]

def approve_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET status = "approved" WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def reject_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
