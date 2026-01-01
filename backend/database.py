import sqlite3
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Use /data path on Render (persistent disk), local path otherwise
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "templates.db"))

# Ensure directory exists
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
logger.info(f"Using database path: {DB_PATH}")

def init_database():
    """Initialize the templates database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            fields TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def save_template(name: str, fields: Dict[str, Any]) -> bool:
    """
    Save or update a template in the database
    
    Args:
        name: Template name (as-is, no underscore conversion)
        fields: Template fields dictionary
        
    Returns:
        bool: True if successful
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        fields_json = json.dumps(fields)
        
        # Try to insert, if name exists, update
        cursor.execute("""
            INSERT INTO templates (name, fields, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                fields = excluded.fields,
                updated_at = excluded.updated_at
        """, (name, fields_json, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        import logging
        logging.error(f"Error saving template: {e}")
        return False

def get_template(name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch template from database by name
    
    Args:
        name: Template name
        
    Returns:
        Dict with fields or None if not found
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT fields FROM templates WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    except Exception as e:
        import logging
        logging.error(f"Error fetching template: {e}")
        return None

def list_templates() -> List[Dict[str, Any]]:
    """
    List all templates in database
    
    Returns:
        List of template info dicts
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, fields, created_at, updated_at 
            FROM templates 
            ORDER BY created_at DESC
        """)
        results = cursor.fetchall()
        
        conn.close()
        
        templates = []
        for row in results:
            name, fields_json, created_at, updated_at = row
            fields = json.loads(fields_json)
            templates.append({
                "name": name,
                "field_count": count_fields(fields),
                "created_at": created_at,
                "updated_at": updated_at
            })
        
        return templates
    except Exception as e:
        import logging
        logging.error(f"Error listing templates: {e}")
        return []

def delete_template(name: str) -> bool:
    """
    Delete a template from database
    
    Args:
        name: Template name
        
    Returns:
        bool: True if successful
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM templates WHERE name = ?", (name,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    except Exception as e:
        import logging
        logging.error(f"Error deleting template: {e}")
        return False

def count_fields(fields_dict: Dict[str, Any]) -> int:
    """Count total number of fields recursively"""
    count = 0
    for value in fields_dict.values():
        if isinstance(value, dict):
            count += count_fields(value)
        else:
            count += 1
    return count

# Initialize database on module import
init_database()
