import os
from dotenv import load_dotenv

load_dotenv()

# App settings
APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

# Model settings
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")

# Performance settings
CPU_THREADS = 10  # adjust based on your CPU (you have 12 cores)
CONTEXT_SIZE = 8192  
# Context window = max tokens model can process at once (input prompt + output)
# 4096 was default, 8192 gives more room for:
#   - Long medical conversations
#   - Large template examples in prompts
#   - Complex multi-field outputs
# Trade-off: Uses more RAM, slightly slower
# Your prompts are ~2500 tokens, so 8192 is comfortable

GPU_LAYERS = 0  # set to 0 for CPU-only, increase if using GPU

# Generation settings
MAX_TOKENS_CLEANER = 1024  # text cleaning output is usually short
MAX_TOKENS_NOTE_GEN = 1536  
# Max output length for generated notes
# 1024 was too conservative - complex templates with many fields need more
# 1536 is a good balance:
#   - Allows detailed notes with all fields filled
#   - Not so high that model rambles or wastes time
#   - Your test output was ~250 tokens, so 1536 has plenty of headroom
# If you see truncated notes, increase to 2048

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

# Document upload settings
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['.pdf', '.docx']
MIN_TEMPLATE_FIELDS = 3
MAX_TEMPLATE_FIELDS = 50
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
RELOAD = False
