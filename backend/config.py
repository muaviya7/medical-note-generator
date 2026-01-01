import os
from dotenv import load_dotenv

load_dotenv()

# App settings
APP_ENV = "production"  # production or development
DATABASE_URL = "sqlite:///./templates.db"  # SQLite database path
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")  # From .env (sensitive)

# Document upload settings
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['.pdf', '.docx']
MIN_TEMPLATE_FIELDS = 3
MAX_TEMPLATE_FIELDS = 50
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

# Server settings
HOST = "0.0.0.0"  # Bind to all interfaces
PORT = 8000  # Server port
RELOAD = False  # Disable auto-reload in production
