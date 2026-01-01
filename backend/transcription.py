# This module handles audio transcription using Whisper or Gemini

import logging
import os
from .LLM.gemini import Gemini
# from .LLM.whisper import Whisper

# Configure logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'transcription.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Gemini
try:
    gemini = Gemini()
    logger.info("Gemini loaded for transcription")
except Exception as e:
    logger.error(f"Failed to load Gemini: {str(e)}")
    gemini = None

# Initialize Whisper (commented out)
# try:
#     whisper = Whisper(model_size="medium", device="cpu", compute_type="int8")
#     logger.info("Whisper model loaded")
# except Exception as e:
#     logger.error(f"Failed to load Whisper: {str(e)}")
#     whisper = None


def transcribe_audio(file_path):
    """
    Transcribe audio file to text using Gemini.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        dict: Dictionary with transcription result
    """
    if gemini is None:
        return {
            'success': False,
            'error': 'Gemini not initialized'
        }
    
    return gemini.gemini_transcribe(file_path)
    
    # Whisper transcription (commented out)
    # if whisper is None:
    #     return {
    #         'success': False,
    #         'error': 'Whisper model not initialized'
    #     }
    # 
    # return whisper.whisper_transcribe(file_path)
