import sqlite3
import os
import datetime

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
    conn.commit()
    conn.close()

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
