# This module handles audio transcription using Whisper

import whisper
from faster_whisper import WhisperModel





#model_name = "./medwhishper_ctranslate2"  # Hugging Face model
#model = WhisperModel(model_name, device="cpu")  # "cpu" if no GPU

model = WhisperModel("medium", device="cpu", compute_type="int8")

audio_path = "C:\\Users\\MUAVIYARASHEED\\Desktop\\test\\0030815.wav"

segments, info = model.transcribe(audio_path)
#result = model.transcribe(audio_path)

print("Transcription Result:\n")
#print(result["text"])
for segment in segments:
    print(segment.text)
def transcribe_audio(file_path):
    # Placeholder for Whisper transcription logic
    return "Transcribed text from audio."