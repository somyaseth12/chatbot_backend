from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
db = SQLAlchemy()

class GPTCache(db.Model):
    __tablename__ = 'gpt_cache'
    id = db.Column(db.Integer, primary_key=True)
    query_hash = db.Column(db.String(128), unique=True, nullable=False , index = True)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GPTCache {self.query_hash[:10]}>"
    def to_dict(self):
        return {
        "query_hash": self.query_hash,
        "response": self.response,
        "timestamp": self.timestamp.isoformat()
    }
    
    import sqlite3

def init_db():
    conn = sqlite3.connect("chatbot_cache.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        rating INTEGER,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS missed_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

    