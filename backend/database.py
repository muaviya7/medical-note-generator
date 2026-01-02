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
    """Initialize the templates database and insert default templates"""
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
    
    # Insert default templates if they don't exist
    default_templates = [
        {
            "name": "general_soap_note",
            "fields": {
                "patient_name": "Full name of the patient",
                "age_gender": "Age and gender of patient",
                "date_of_visit": "Visit date in DD-MMM-YYYY or format shown",
                "chief_complaint": "Main reason for visit or primary symptom",
                "history_of_present_illness": "Detailed description of current symptoms and timeline",
                "relevant_medical_history": "Previous medical conditions, surgeries, or chronic illnesses",
                "current_medications_allergies": "List of current medications with dosage and known allergies",
                "physical_examination": {
                    "vital_signs": {
                        "temperature": "Body temperature in F or C",
                        "blood_pressure": "BP reading in mmHg format (systolic/diastolic)",
                        "heart_rate": "Pulse rate in beats per minute (bpm)",
                        "respiratory_rate": "Breathing rate per minute",
                        "oxygen_saturation": "O2 saturation percentage on room air or supplemental O2"
                    },
                    "general_findings": "Overall physical exam findings and observations"
                },
                "assessment": "Doctor's diagnosis or clinical impression",
                "plan": "Treatment plan, prescriptions, and recommendations",
                "follow_up": "Follow-up instructions and timeline"
            }
        },
        {
            "name": "cardiology_consultation",
            "fields": {
                "patient_information": {
                    "name": "Full name of the patient",
                    "age": "Patient's age in years",
                    "gender": "Gender - Male/Female/Other"
                },
                "date_of_visit": "Visit date in DD-MMM-YYYY format",
                "chief_complaint": "Primary cardiac-related complaint or reason for visit",
                "history_of_present_illness": "Detailed description of cardiac symptoms, onset, duration, and progression",
                "cardiac_history": {
                    "previous_cardiac_events": "Previous heart attacks, angina, arrhythmias, or cardiac procedures",
                    "risk_factors": "Hypertension, diabetes, hyperlipidemia, smoking, family history"
                },
                "current_medications": "List of current cardiac medications with dosages",
                "physical_examination": {
                    "vital_signs": {
                        "blood_pressure": "BP reading in mmHg format (systolic/diastolic)",
                        "heart_rate": "Pulse rate in beats per minute",
                        "respiratory_rate": "Breathing rate per minute",
                        "oxygen_saturation": "O2 saturation percentage",
                        "temperature": "Body temperature"
                    },
                    "cardiovascular_exam": {
                        "heart_sounds": "Description of S1, S2, and any murmurs or gallops",
                        "peripheral_pulses": "Quality and symmetry of peripheral pulses",
                        "edema": "Presence and location of edema",
                        "jvd": "Jugular venous distension findings"
                    },
                    "respiratory_exam": "Lung sounds and respiratory findings"
                },
                "diagnostic_tests": {
                    "ecg_findings": "Electrocardiogram results and interpretation",
                    "echocardiogram": "Echo findings if available",
                    "lab_results": "Troponin, BNP, lipid panel, and other relevant labs",
                    "imaging": "Chest X-ray or other cardiac imaging findings"
                },
                "assessment": {
                    "diagnosis": "Primary cardiac diagnosis",
                    "severity": "Severity assessment and classification"
                },
                "treatment_plan": {
                    "medications": "New or adjusted cardiac medications",
                    "procedures": "Recommended procedures or interventions",
                    "lifestyle_modifications": "Diet, exercise, and lifestyle recommendations"
                },
                "follow_up": "Follow-up timeline and monitoring plan"
            }
        }
    ]
    
    for template in default_templates:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO templates (name, fields, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (template["name"], json.dumps(template["fields"]), datetime.now(), datetime.now()))
            logger.info(f"Default template '{template['name']}' ensured in database")
        except Exception as e:
            logger.error(f"Error inserting default template '{template['name']}': {e}")
    
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
