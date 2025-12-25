# This module handles audio transcription using Whisper

import whisper
from faster_whisper import WhisperModel
import logging
import os
from pathlib import Path
import sys
import time

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

try:
    # Initialize Whisper model
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    logger.info("Whisper model loaded")
    
except Exception as e:
    logger.error(f"Failed to load Whisper model: {str(e)}", exc_info=True)
    model = None
    sys.exit(1)


def transcribe_audio(file_path):
    """
    Transcribe audio file to text using Whisper model.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        dict: Dictionary with keys:
            - 'success' (bool): Whether transcription succeeded
            - 'text' (str): Transcribed text (or error message if failed)
            - 'segments' (int): Number of segments processed
            - 'duration' (float): Audio duration in seconds
            - 'language' (str): Detected language
            - 'file_size_mb' (float): File size in MB
            - 'error' (str): Error message if failed
    """
    result = {
        'success': False,
        'text': '',
        'segments': 0,
        'duration': 0,
        'language': '',
        'file_size_mb': 0,
        'error': ''
    }
    
    try:
        print(f"\n Starting transcription...")
        
        # Validate file path
        if not file_path:
            raise ValueError("File path cannot be empty")
        
        file_path = str(file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            error_msg = f"Audio file not found: {file_path}"
            logger.error(error_msg)
            print(f"❌ Error: {error_msg}")
            raise FileNotFoundError(error_msg)
        
        # Check file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024*1024)
        result['file_size_mb'] = file_size_mb
        print(f"📦 File size: {file_size_mb:.2f} MB")
        
        if file_size == 0:
            raise ValueError("Audio file is empty")
        
        # Check if model is loaded
        if model is None:
            error_msg = "Whisper model not initialized"
            logger.error(error_msg)
            print(f"❌ Error: {error_msg}")
            raise RuntimeError(error_msg)
        
        # Transcribe audio
        logger.info(f"Transcribing audio file...")
        print(f" Transcribing audio...\n")
        start_time = time.time()
        segments, info = model.transcribe(file_path)
        
        # Extract and combine text
        result['duration'] = info.duration
        result['language'] = info.language
        
        transcribed_text = ""
        segment_count = 0
        
        for segment in segments:
            transcribed_text += segment.text + " "
            print(segment.text, end=" ", flush=True)
            segment_count += 1
        elapsed_time = time.time() - start_time
        print(f"\n\n🌍 Language: {info.language} | ⏱️  Duration: {info.duration:.2f}s")
        transcribed_text = transcribed_text.strip()
        result['text'] = transcribed_text
        result['segments'] = segment_count
        result['success'] = True
        
        logger.info(f"✓ Transcription completed: {segment_count} segments, {len(transcribed_text)} characters")
        print(f"✅ Transcription completed: {segment_count} segments, {len(transcribed_text)} characters")
        print(f" Transcription time: {elapsed_time:.2f}s")
        return result
        
    except FileNotFoundError as e:
        error_msg = f"File error: {str(e)}"
        logger.error(error_msg)
        result['error'] = error_msg
        print(f"❌ {error_msg}")
        return result
    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(error_msg)
        result['error'] = error_msg
        print(f"❌ {error_msg}")
        return result
    except RuntimeError as e:
        error_msg = f"Runtime error: {str(e)}"
        logger.error(error_msg)
        result['error'] = error_msg
        print(f"❌ {error_msg}")
        return result
    except Exception as e:
        error_msg = f"Unexpected error during transcription: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result['error'] = error_msg
        print(f"❌ {error_msg}")
        return result


# Test code
if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("Running transcription test...")
        print("="*60)
        
        test_audio_path = r"C:\Users\Bilal rashid\Downloads\audio\transcription_test_2min.wav"
        
        if os.path.exists(test_audio_path):
            result = transcribe_audio(test_audio_path)
            
            if result['success']:
                print(f"\n{'='*60}")
                print("📄 TRANSCRIPTION RESULT:")
                print(f"{'='*60}")
                print(result['text'])
                print(f"{'='*60}")
                print(f"Segments: {result['segments']} | Language: {result['language']} | Duration: {result['duration']:.2f}s")
                print(f"{'='*60}\n")
            else:
                print(f"\n Failed: {result['error']}\n")
        else:
            print(f"\n Test file not found: {test_audio_path}\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\n Error: {str(e)}\n")