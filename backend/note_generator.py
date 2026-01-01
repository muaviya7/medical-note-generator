# This module generates structured medical notes from text
import logging
import os
import json
import time
from pydantic import BaseModel
from typing import Dict, Any
from .LLM.gemini import Gemini
from .database import get_template

# Pydantic Models
class GenerateNoteRequest(BaseModel):
    cleaned_text: str
    template_name: str

class GenerateNoteResponse(BaseModel):
    success: bool
    medical_note: Dict[str, Any] = {}
    time_elapsed: float = 0.0
    formatted_html: str = ""
    error: str | None = None

# Configure logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'note_generator.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Gemini
try:
    gemini = Gemini()
    logger.info("Gemini initialized for note generation")
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {str(e)}")
    gemini = None


def load_template(template_name):
    """
    Load a template from database by name
    
    Args:
        template_name: Name of template (no .json extension needed)
        
    Returns:
        Dict with template fields or None if not found
    """
    # Remove .json extension if present
    if template_name.endswith('.json'):
        template_name = template_name[:-5]
    
    # Fetch from database
    template_fields = get_template(template_name)
    
    if template_fields:
        logger.info(f"Loaded template '{template_name}' from database")
        return template_fields
    
    logger.error(f"Template '{template_name}' not found in database")
    return None


def generate_note_from_text(cleaned_text, template_json):
    """
    Generate structured medical note from cleaned text using template
    
    Args:
        cleaned_text: The cleaned medical conversation text
        template_json: JSON template (dict or path to file)
    
    Returns:
        dict: Generated medical note following template structure
    """
    if gemini is None:
        logger.error("Gemini not initialized")
        return {"error": "Gemini not available"}
    
    # Load template if it's a filename
    if isinstance(template_json, str):
        template_json = load_template(template_json)
        if template_json is None:
            return {"error": "Failed to load template"}
    
    try:
        logger.info("Generating medical note...")
        start_time = time.time()
        
        generated_text = gemini.gemini_generate_note(cleaned_text, template_json)
        elapsed = time.time() - start_time
        
        logger.info(f"Generated text length: {len(generated_text)} characters")
        logger.info(f"Generation took {elapsed:.2f} seconds")
        
        if not generated_text:
            logger.error("Model returned empty response!")
            return {"error": "Model generated empty output"}
        
        logger.info(f"Response preview: {generated_text[:200]}...")
        
        # Minimal cleanup - just find JSON boundaries if model adds anything
        if '{' in generated_text:
            start = generated_text.find('{')
            end = generated_text.rfind('}') + 1
            json_text = generated_text[start:end]
        else:
            json_text = generated_text
        
        # Parse JSON
        try:
            note_json = json.loads(json_text)
            logger.info("Successfully parsed JSON response")
            note_json['_generation_time'] = f"{elapsed:.2f}s"
            return note_json
            
        except json.JSONDecodeError as je:
            logger.error(f"JSON parse failed: {str(je)}")
            logger.error(f"Raw output: {generated_text[:500]}")
            return {
                "error": "Model did not return valid JSON", 
                "raw_output": generated_text,
                "parse_error": str(je),
                "_generation_time": f"{elapsed:.2f}s"
            }
            
    except Exception as e:
        logger.error(f"Error during note generation: {str(e)}")
        return {"error": str(e)}


# Test case
