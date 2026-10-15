import sqlite3
import json
import os
from datetime import datetime
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            original_file_path TEXT,
            cleaned_file_path TEXT,
            pdf_report_path TEXT,
            raw_score REAL,
            cleaned_score REAL,
            rows_before INTEGER,
            rows_after INTEGER,
            cols_count INTEGER,
            issues_count INTEGER,
            actions_json TEXT,
            status TEXT DEFAULT 'Completed'
        )
    ''')
    conn.commit()
    conn.close()

def save_history_record(session_id, filename, original_file_path, cleaned_file_path, pdf_report_path,
                        raw_score, cleaned_score, rows_before, rows_after, cols_count, issues_count, actions_list):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO processing_history (
            session_id, filename, upload_time, original_file_path, cleaned_file_path, pdf_report_path,
            raw_score, cleaned_score, rows_before, rows_after, cols_count, issues_count, actions_json, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        filename,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        original_file_path,
        cleaned_file_path,
        pdf_report_path,
        raw_score,
        cleaned_score,
        rows_before,
        rows_after,
        cols_count,
        issues_count,
        json.dumps(actions_list),
        'Completed'
    ))
    conn.commit()
    conn.close()

def get_all_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM processing_history ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    history_list = []
    for r in rows:
        item = dict(r)
        if item.get('actions_json'):
            try:
                item['actions'] = json.loads(item['actions_json'])
            except Exception:
                item['actions'] = []
        else:
            item['actions'] = []
        history_list.append(item)
    return history_list

def get_history_by_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM processing_history WHERE session_id = ?', (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        item = dict(row)
        if item.get('actions_json'):
            try:
                item['actions'] = json.loads(item['actions_json'])
            except Exception:
                item['actions'] = []
        return item
    return None
