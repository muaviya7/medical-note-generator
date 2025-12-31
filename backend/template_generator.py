# Generate and save medical note templates
import os
import json
import logging
import re
from pydantic import BaseModel
from typing import Dict, Any, List
from llama_cpp import Llama
from .prompts import template_extraction_prompt
from .config import (
    MODEL_PATH, CPU_THREADS, CONTEXT_SIZE, GPU_LAYERS,
    MAX_TOKENS_NOTE_GEN, TEMPERATURE, TOP_P, REPEAT_PENALTY,
    MIN_TEMPLATE_FIELDS, MAX_TEMPLATE_FIELDS, TEMPLATE_DIR
)
from .database import save_template as db_save_template

# Pydantic Models
class CreateTemplateResponse(BaseModel):
    success: bool
    template_name: str = ""
    fields: Dict[str, Any] = {}
    time_elapsed: float = 0.0
    message: str | None = None
    error: str | None = None

class TemplateInfo(BaseModel):
    name: str
    display_name: str
    field_count: int

class ListTemplatesResponse(BaseModel):
    success: bool
    templates: List[TemplateInfo] = []
    error: str = ""

class GetTemplateResponse(BaseModel):
    success: bool
    template: Dict[str, Any] = {}
    error: str = ""

class DeleteTemplateResponse(BaseModel):
    success: bool
    message: str = ""
    error: str = ""

logger = logging.getLogger(__name__)

# Load model (reuse same instance)
try:
    model = Llama(
        model_path=MODEL_PATH,
        n_ctx=CONTEXT_SIZE,
        n_threads=CPU_THREADS,
        n_gpu_layers=GPU_LAYERS,
        verbose=False
    )
    logger.info("Model loaded for template generation")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    model = None


def validate_template_name(name):
    """
    Validate and sanitize template name
    
    Args:
        name: User-provided template name
        
    Returns:
        tuple: (is_valid: bool, sanitized_name: str, error: str)
    """
    if not name or len(name.strip()) == 0:
        return False, "", "Template name cannot be empty"
    
    name = name.strip()
    
    if len(name) > 50:
        return False, "", "Template name too long (max 50 characters)"
    
    # Sanitize: keep alphanumeric, spaces, hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-]', '', name)
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    sanitized = sanitized.lower()
    
    if not sanitized:
        return False, "", "Template name must contain letters or numbers"
    
    return True, sanitized, ""


def template_exists(template_name):
    """
    Check if template file already exists
    
    Args:
        template_name: Sanitized template name
        
    Returns:
        bool: True if exists
    """
    template_path = os.path.join(TEMPLATE_DIR, f"{template_name}.json")
    return os.path.exists(template_path)


def generate_template_fields(document_text):
    """
    Use AI to extract field names from document text
    
    Args:
        document_text: Extracted text from document
        
    Returns:
        dict: {"success": bool, "fields": dict, "error": str}
    """
    result = {
        "success": False,
        "fields": {},
        "error": ""
    }
    
    try:
        if not model:
            raise RuntimeError("Model not loaded")
        
        if not document_text or len(document_text) < 50:
            raise ValueError("Document text too short to analyze")
        
        prompt = template_extraction_prompt(document_text)
        
        response = model(
            prompt,
            max_tokens=1024,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            repeat_penalty=REPEAT_PENALTY,
            echo=False
        )
        
        generated_text = response['choices'][0]['text'].strip()
        
        # Extract JSON object - find first complete JSON by counting braces
        start_idx = generated_text.find('{')
        if start_idx == -1:
            raise ValueError("No JSON found in model output")
        
        # Find matching closing brace
        brace_count = 0
        end_idx = -1
        for i in range(start_idx, len(generated_text)):
            if generated_text[i] == '{':
                brace_count += 1
            elif generated_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx == -1:
            raise ValueError("No matching closing brace found in JSON")
        
        json_text = generated_text[start_idx:end_idx + 1]
        
        # Parse fields
        fields = json.loads(json_text)
        
        if not isinstance(fields, dict):
            raise ValueError("AI did not return a dict of fields")
        
        # Count total fields (including nested)
        def count_fields(obj):
            count = 0
            for value in obj.values():
                if isinstance(value, dict):
                    count += count_fields(value)
                else:
                    count += 1
            return count
        
        field_count = count_fields(fields)
        
        result["success"] = True
        result["fields"] = fields
        logger.info(f"Template fields extracted: {field_count}")
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse AI response: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"JSON text: {json_text if 'json_text' in locals() else 'N/A'}")
        result["error"] = error_msg
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Field extraction error: {error_msg}")
        result["error"] = error_msg
    
    return result


def save_template(template_name, display_name, fields):
    """
    Save template to JSON file
    
    Args:
        template_name: Sanitized filename
        display_name: User-friendly display name
        fields: List of field names
        
    Returns:
        dict: {"success": bool, "path": str, "error": str}
    """
    result = {
        "success": False,
        "path": "",
        "error": ""
    }
    
    try:
        # Create templates directory if needed
        os.makedirs(TEMPLATE_DIR, exist_ok=True)
        
        template_path = os.path.join(TEMPLATE_DIR, f"{template_name}.json")
        
        # Check if exists
        if os.path.exists(template_path):
            raise FileExistsError(f"Template '{template_name}' already exists")
        
        # Create template structure
        template_data = {
            "template": display_name,
            "fields": fields
        }
        
        with open(template_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        result["success"] = True
        result["path"] = template_path
        logger.info(f"Template saved: {os.path.basename(template_path)}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Template save error: {error_msg}")
        result["error"] = error_msg
    
    return result


def create_template_from_document(file_path, template_name):
    """
    Complete workflow: extract text → generate fields → save template to database
    
    Args:
        file_path: Path to PDF/DOCX file
        template_name: User-provided template name (stored as-is, no underscore conversion)
        
    Returns:
        dict: {"success": bool, "fields": dict, "template_name": str, "error": str}
    """
    from .document_processor import extract_text
    
    result = {
        "success": False,
        "fields": {},
        "template_name": "",
        "error": ""
    }
    
    try:
        # Extract text from document
        extract_result = extract_text(file_path)
        
        if not extract_result["success"]:
            raise ValueError(extract_result["error"])
        
        document_text = extract_result["text"]
        
        # Generate template fields using AI
        fields_result = generate_template_fields(document_text)
        
        if not fields_result["success"]:
            raise ValueError(fields_result["error"])
        
        fields = fields_result["fields"]
        
        # Save to database (template_name stored as-is)
        if not db_save_template(template_name, fields):
            raise ValueError("Failed to save template to database")
        
        result["success"] = True
        result["fields"] = fields
        result["template_name"] = template_name
        
        logger.info(f"Template '{template_name}' created successfully with {len(fields)} fields")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Template creation error: {error_msg}")
        result["error"] = error_msg
    
    return result


# Test
