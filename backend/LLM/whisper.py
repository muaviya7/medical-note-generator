from faster_whisper import WhisperModel
import logging
import os
import time

logger = logging.getLogger(__name__)


class Whisper:
    """Whisper model class for audio transcription"""
    
    def __init__(self, model_size="medium", device="cpu", compute_type="int8"):
        """
        Initialize Whisper model
        
        Args:
            model_size: Size of Whisper model (tiny, base, small, medium, large)
            device: Device to run on (cpu or cuda)
            compute_type: Computation type (int8, float16, float32)
        """
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            logger.info(f"Whisper model loaded: {model_size}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
    
    def whisper_transcribe(self, audio_file_path):
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            dict: Transcription result with keys:
                - success (bool): Whether transcription succeeded
                - text (str): Transcribed text
                - segments (int): Number of segments
                - duration (float): Audio duration in seconds
                - language (str): Detected language
                - file_size_mb (float): File size in MB
                - error (str): Error message if failed
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
            # Validate file
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                raise ValueError("Audio file is empty")
            
            result['file_size_mb'] = file_size / (1024 * 1024)
            
            # Transcribe
            logger.info(f"Transcribing audio file: {audio_file_path}")
            start_time = time.time()
            
            segments, info = self.model.transcribe(
                audio_file_path,
                beam_size=5,
                language=None,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Collect segments
            transcribed_text = []
            segment_count = 0
            
            for segment in segments:
                transcribed_text.append(segment.text)
                segment_count += 1
            
            elapsed_time = time.time() - start_time
            
            result.update({
                'success': True,
                'text': ' '.join(transcribed_text).strip(),
                'segments': segment_count,
                'duration': info.duration,
                'language': info.language,
                'time_elapsed': elapsed_time
            })
            
            logger.info(f"Transcription completed in {elapsed_time:.2f}s")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Transcription failed: {error_msg}")
            result['error'] = error_msg
        
        return result
