import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # From .env (sensitive)
GEMINI_MODEL = "gemini-2.5-flash"  # Default model for note generation
GEMINI_TRANSCRIPTION_MODEL = "gemini-2.5-flash"  # Default model for transcription

# Generation settings
MAX_TOKENS_CLEANER = 1024  # text cleaning output is usually short
MAX_TOKENS_NOTE_GEN = 2048  # Gemini can handle larger outputs efficiently
MAX_TOKENS_TRANSCRIPTION = 2048  # Audio transcription output

# Model behavior parameters
TEMPERATURE = 0.2  
# Controls randomness: 0.0 = deterministic/consistent, 1.0 = creative/random
# Lower = more predictable medical notes (recommended for clinical docs)

TOP_P = 0.95  
# Nucleus sampling: considers only top tokens that add up to this probability
# 0.95 = considers 95% most likely tokens, filters out unlikely ones
# Helps prevent weird/nonsensical outputs while keeping some variety

REPEAT_PENALTY = 1.1  
# Penalizes repeating the same words/phrases
# 1.0 = no penalty, >1.0 = discourages repetition
# Prevents model from getting stuck in loops like "patient patient patient..."
