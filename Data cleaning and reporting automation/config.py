import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'autoclean_secret_key_2026_msc_project')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed')
    DATABASE_PATH = os.path.join(BASE_DIR, 'history.db')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max upload limit
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Ensure required directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
