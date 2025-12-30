# This module generates structured medical notes from text
from llama_cpp import Llama
import logging
import os
import sys
import json
import time
from pydantic import BaseModel
from typing import Dict, Any
from .prompts import note_generator_prompt
from .config import (
    MODEL_PATH, CPU_THREADS, CONTEXT_SIZE, GPU_LAYERS,
    MAX_TOKENS_NOTE_GEN, TEMPERATURE, TOP_P, REPEAT_PENALTY
)
from .database import get_template

# Pydantic Models
class GenerateNoteRequest(BaseModel):
    cleaned_text: str
    template_name: str

class GenerateNoteResponse(BaseModel):
    success: bool
    medical_note: Dict[str, Any] = {}
    time_elapsed: float = 0.0
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

try:
    # Initialize Mistral model
    model = Llama(
        model_path=MODEL_PATH,
        n_ctx=CONTEXT_SIZE,
        n_threads=CPU_THREADS,
        n_gpu_layers=GPU_LAYERS,
        verbose=False
    )
    
except Exception as e:
    logger.error(f"Failed to load Mistral model: {str(e)}", exc_info=True)
    model = None
    sys.exit(1)


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
    if model is None:
        logger.error("Model not loaded, cannot generate note")
        return {"error": "Model not available"}
    
    # Load template if it's a filename
    if isinstance(template_json, str):
        template_json = load_template(template_json)
        if template_json is None:
            return {"error": "Failed to load template"}
    
    try:
        # Get the prompt
        prompt = note_generator_prompt(cleaned_text, template_json)
        
        logger.info("Generating medical note...")
        logger.info(f"Prompt length: {len(prompt)} characters")
        
        start_time = time.time()
        
        # Generate response
        response = model(
            prompt,
            max_tokens=MAX_TOKENS_NOTE_GEN,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            repeat_penalty=REPEAT_PENALTY,
            echo=False
        )
        
        elapsed = time.time() - start_time
        
        generated_text = response['choices'][0]['text'].strip()
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
