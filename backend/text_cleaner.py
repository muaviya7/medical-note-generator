# This module handles medical text cleaning and restructuring using Gemini

import logging
import os
import time
from pydantic import BaseModel
from .LLM.gemini import Gemini

# Pydantic Models
class CleanTextRequest(BaseModel):
    transcribed_text: str

class CleanTextResponse(BaseModel):
    success: bool
    cleaned_text: str = ""
    time_elapsed: float = 0.0
    error: str = ""

# Configure logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'text_cleaner.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Gemini
try:
    gemini = Gemini()
    logger.info("Gemini initialized for text cleaning")
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {str(e)}")
    gemini = None


def format_text(transcribed_text):
    """
    Format and clean transcribed medical text.
    
    Args:
        transcribed_text (str): Raw transcribed text
        
    Returns:
        str: Formatted and cleaned text
    """
    try:
        if not transcribed_text:
            raise ValueError("Input text is empty")
        
        if gemini is None:
            raise RuntimeError("Gemini not initialized")
        
        start_time = time.time()
        formatted_text = gemini.gemini_clean_text(transcribed_text)
        elapsed = time.time() - start_time
        
        logger.info(f"Formatted: {len(formatted_text)} chars in {elapsed:.2f}s")
        
        return formatted_text
        
    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(error_msg)
        return None
    except RuntimeError as e:
        error_msg = f"Runtime error: {str(e)}"
        logger.error(error_msg)
        return None
    except Exception as e:
        error_msg = f"Formatting error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None


def clean_text(transcribed_text):
    """
    Clean and format transcribed medical text.
    
    Args:
        transcribed_text (str): Raw transcribed text
        
    Returns:
        dict: Result with keys 'success', 'formatted_text', 'error'
    """
    result = {
        'success': False,
        'formatted_text': '',
        'error': ''
    }
    
    try:
        formatted = format_text(transcribed_text)
        if formatted is None:
            raise ValueError("Formatting failed")
        
        result['formatted_text'] = formatted
        result['success'] = True
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Pipeline error: {error_msg}", exc_info=True)
        result['error'] = error_msg
        return result
