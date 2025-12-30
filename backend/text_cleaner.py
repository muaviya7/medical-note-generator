# This module handles medical text cleaning and restructuring using Mistral

from llama_cpp import Llama
import logging
import os
import sys
import time
from pydantic import BaseModel
from .prompts import text_cleaner_prompt
from .config import (
    MODEL_PATH, CPU_THREADS, CONTEXT_SIZE, GPU_LAYERS,
    MAX_TOKENS_CLEANER, TEMPERATURE, TOP_P, REPEAT_PENALTY
)

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
#test trasncribed text
transcribed_text = "uh okay so patient is a 45 year old male um came in today complaining of fever and uh cough since like past three days he says the fever is around one zero one maybe one zero two degrees uh fahrenheit mostly in evenings um also complaining of body aches and uh mild headache no chest pain uh no shortness of breath denies nausea vomiting or diarrhea patient says he has been taking paracetamol five hundred mg like two times a day which gives temporary relief um he uh denies any known allergies no history of diabetes or hypertension uh vitals today temperature is one zero one point four blood pressure one three zero over eight five pulse around ninety two respiratory rate eighteen oxygen saturation ninety eight percent on room air uh lungs clear on auscultation no wheezing uh heart sounds normal abdomen soft non tender uh plan is to uh start patient on azithromycin five hundred mg once daily for three days advise fluids rest and follow up in three days if symptoms persistor worsen"  
def format_text(transcribed_text):
    """
    First pass: Format and clean transcribed medical text.
    
    Args:
        transcribed_text (str): Raw transcribed text
        
    Returns:
        str: Formatted and cleaned text
    """
    try:
        print("\nFormatting text...\n")
        
        if not transcribed_text:
            raise ValueError("Input text is empty")
        
        if model is None:
            raise RuntimeError("Mistral model not initialized")
        
        prompt = text_cleaner_prompt(transcribed_text)
        start_time = time.time()
        response = model(
            prompt,
            max_tokens=2048,
            temperature=0.3,
            top_p=0.9
        )
        
        formatted_text = response['choices'][0]['text'].strip()
        
        # Display output in segments (sentence by sentence)
        sentences = formatted_text.split('. ')
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                print(sentence + '. ', end='', flush=True)
        print()  # New line after output
        
        elapsed_time = time.time() - start_time
        logger.info(f"✓ Formatted: {len(formatted_text)} chars in {elapsed_time:.2f}s")
        print(f"\n Formatting complete ({elapsed_time:.2f}s)")
        
        return formatted_text
        
    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(error_msg)
        print(f" {error_msg}")
        return None
    except RuntimeError as e:
        error_msg = f"Runtime error: {str(e)}"
        logger.error(error_msg)
        print(f" {error_msg}")
        return None
    except Exception as e:
        error_msg = f"Formatting error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"❌ {error_msg}")
        return None
    '''
    def restructure_text(formatted_text):
    """
    Second pass: Restructure into medical note format.
    
    Args:
        formatted_text (str): Formatted text
        
    Returns:
        str: Restructured medical note in SOAP format
    """
    try:
        print("\n📋 Restructuring into medical format...")
        
        if not formatted_text:
            raise ValueError("Input text is empty")
        
        if model is None:
            raise RuntimeError("Mistral model not initialized")
        
        restructure_prompt = f"""You are a medical documentation expert. Restructure this text into SOAP format:

S (Subjective): Patient's complaints and symptoms
O (Objective): Vital signs, measurements, observations
A (Assessment): Diagnosis or clinical impression
P (Plan): Treatment and follow-up

Medical text:
{formatted_text}

SOAP Note:"""

        response = model(
            restructure_prompt,
            max_tokens=2048,
            temperature=0.3,
            top_p=0.9
        )
        
        structured_text = response['choices'][0]['text'].strip()
        logger.info(f"✓ Text restructured: {len(structured_text)} characters")
        print(f"✅ Restructuring complete")
        
        return structured_text
        
    except Exception as e:
        logger.error(f"Restructuring error: {str(e)}")
        print(f"❌ Restructuring failed: {str(e)}")
        return formatted_text
'''
def clean_text(transcribed_text):
    """
    Pipeline: Format medical text.
    
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
        # Format text
        formatted = format_text(transcribed_text)
        if formatted is None:
            raise ValueError("Formatting failed - returned None")
        
        result['formatted_text'] = formatted
        result['success'] = True
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Pipeline error: {error_msg}", exc_info=True)
        result['error'] = error_msg
        print(f"❌ Pipeline error: {error_msg}")
        return result


# Test code
