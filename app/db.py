import os
import psycopg2

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            ip TEXT,
            country TEXT,
            device TEXT,
            hour INT,
            failed_attempts INT,
            risk_score INT,
            decision TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_event(event, score, decision):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO events (user_id, ip, country, device, hour, failed_attempts, risk_score, decision)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        event["user_id"],
        event["ip"],
        event["country"],
        event["device"],
        event["hour"],
        event["failed_attempts"],
        score,
        decision
    ))
    conn.commit()
    cur.close()
    conn.close()

def get_user_history(user_id, minutes=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ip, country, hour, failed_attempts, created_at
        FROM events
        WHERE user_id = %s
        AND created_at > NOW() - INTERVAL '%s minutes'
        ORDER BY created_at DESC
    """, (user_id, minutes))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
