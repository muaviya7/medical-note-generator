from google import genai
from google.genai import types
import logging
import time
from .config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TRANSCRIPTION_MODEL,
    MAX_TOKENS_CLEANER, MAX_TOKENS_NOTE_GEN, MAX_TOKENS_TRANSCRIPTION,
    TEMPERATURE, TOP_P
)

logger = logging.getLogger(__name__)


class Gemini:
    """Gemini AI model class for medical text processing"""
    
    # Fallback models to try when rate limit is hit
    FALLBACK_MODELS = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.0-flash"
    ]
    
    def __init__(self):
        """Initialize Gemini client"""
        try:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.default_model = GEMINI_MODEL
            self.transcription_model = GEMINI_TRANSCRIPTION_MODEL
            logger.info(f"Gemini initialized with model: {self.default_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            raise
    
    def _is_rate_limit_error(self, error):
        """Check if error is a rate limit error"""
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in [
            'rate limit', 'quota', 'resource exhausted', '429', 'too many requests'
        ])
    
    def _call_api_with_retry(self, model, contents, max_tokens, temperature=None, top_p=None, max_retries=3):
        """
        Call Gemini API with retry logic and model fallback for rate limits
        
        Args:
            model: Model name to use
            contents: Text prompt string OR list [prompt, file] for multimodal
            max_tokens: Maximum output tokens
            temperature: Temperature (optional, uses config default)
            top_p: Top P (optional, uses config default)
            max_retries: Number of retry attempts per model
            
        Returns:
            str: Generated text
        """
        models_to_try = [model] + [m for m in self.FALLBACK_MODELS if m != model]
        
        for model_name in models_to_try:
            retry_delay = 2
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=temperature or TEMPERATURE,
                            top_p=top_p or TOP_P,
                            max_output_tokens=max_tokens
                        )
                    )
                    
                    if model_name != model:
                        logger.info(f"Successfully used fallback model: {model_name}")
                    
                    return response.text.strip()
                    
                except Exception as api_error:
                    last_error = api_error
                    error_msg = str(api_error)
                    
                    if self._is_rate_limit_error(api_error):
                        logger.warning(f"Rate limit hit on {model_name}, trying next model...")
                        break
                    
                    # Network errors - retry same model
                    if "10013" in error_msg or "11001" in error_msg or "timeout" in error_msg.lower():
                        if attempt < max_retries - 1:
                            logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {error_msg}")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                    
                    raise
            
            if last_error and not self._is_rate_limit_error(last_error):
                raise last_error
        
        raise Exception(f"API rate limit exceeded on all models. Models tried: {', '.join(models_to_try)}")
    
    def gemini_clean_text(self, transcribed_text, model=None):
        """
        Clean and format transcribed medical text
        
        Args:
            transcribed_text: Raw transcribed text
            model: Model name (optional, uses default if None)
            
        Returns:
            str: Cleaned and formatted text
        """
        if model is None:
            model = self.default_model
        
        from backend.prompts import text_cleaner_prompt
        prompt = text_cleaner_prompt(transcribed_text)
        
        return self._call_api_with_retry(model, prompt, MAX_TOKENS_CLEANER)
    
    def gemini_generate_note(self, cleaned_text, template_json, model=None):
        """
        Generate structured medical note from cleaned text
        
        Args:
            cleaned_text: Cleaned medical text
            template_json: Template structure (dict)
            model: Model name (optional, uses default if None)
            
        Returns:
            str: Generated note as JSON string
        """
        if model is None:
            model = self.default_model
        
        from backend.prompts import note_generator_prompt
        prompt = note_generator_prompt(cleaned_text, template_json)
        
        return self._call_api_with_retry(model, prompt, MAX_TOKENS_NOTE_GEN)
    
    def gemini_create_template(self, document_text, model=None):
        """
        Extract template structure from document
        
        Args:
            document_text: Medical document text
            model: Model name (optional, uses default if None)
            
        Returns:
            str: Template structure as JSON string
        """
        if model is None:
            model = self.default_model
        
        from backend.prompts import template_extraction_prompt
        prompt = template_extraction_prompt(document_text)
        
        return self._call_api_with_retry(model, prompt, MAX_TOKENS_NOTE_GEN)
    
    def gemini_transcribe(self, audio_file_path, model=None):
        """
        Transcribe audio using Gemini
        
        Args:
            audio_file_path: Path to audio file
            model: Model name (optional, uses transcription model if None)
            
        Returns:
            dict: Transcription result with keys:
                - success (bool): Whether transcription succeeded
                - text (str): Transcribed text
                - file_size_mb (float): File size in MB
                - error (str): Error message if failed
        """
        import os
        from backend.prompts import audio_transcription_prompt
        
        result = {
            'success': False,
            'text': '',
            'file_size_mb': 0,
            'error': ''
        }
        
        try:
            if model is None:
                model = self.transcription_model
            
            # Validate file
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                raise ValueError("Audio file is empty")
            
            result['file_size_mb'] = file_size / (1024 * 1024)
            
            logger.info(f"Transcribing audio with Gemini: {audio_file_path}")
            
            # Determine MIME type
            import mimetypes
            mime_type, _ = mimetypes.guess_type(audio_file_path)
            if mime_type is None:
                ext = os.path.splitext(audio_file_path)[1].lower()
                mime_map = {
                    '.wav': 'audio/wav',
                    '.mp3': 'audio/mpeg',
                    '.m4a': 'audio/mp4',
                    '.ogg': 'audio/ogg',
                    '.flac': 'audio/flac',
                    '.webm': 'audio/webm'
                }
                mime_type = mime_map.get(ext, 'audio/wav')
            
            # Upload file to Gemini with display name to help with type detection
            file_name = os.path.basename(audio_file_path)
            with open(audio_file_path, 'rb') as audio:
                # Create file with metadata
                from google.genai.types import UploadFileConfig
                config = UploadFileConfig(mime_type=mime_type, display_name=file_name)
                audio_file = self.client.files.upload(file=audio, config=config)
            logger.info(f"File uploaded: {audio_file.name}")
            
            # Wait for file to be processed
            import time
            while audio_file.state == "PROCESSING":
                time.sleep(2)
                audio_file = self.client.files.get(name=audio_file.name)
            
            if audio_file.state == "FAILED":
                raise RuntimeError("Gemini failed to process audio file")
            
            # Transcribe using unified API method with fallback
            from backend.prompts import audio_transcription_prompt
            transcribed_text = self._call_api_with_retry(
                model=model,
                contents=[audio_transcription_prompt(), audio_file],
                max_tokens=MAX_TOKENS_TRANSCRIPTION,
                temperature=0.1
            )
            
            # Clean up uploaded file
            self.client.files.delete(name=audio_file.name)
            
            result.update({
                'success': True,
                'text': transcribed_text
            })
            
            logger.info(f"Gemini transcription completed: {len(transcribed_text)} characters")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini transcription failed: {error_msg}")
            result['error'] = error_msg
            return result
