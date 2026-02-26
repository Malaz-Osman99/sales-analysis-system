import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env (لأمان المعلومات)
load_dotenv()

class Config:
    """الإعدادات الأساسية للتطبيق"""
    
    # مفتاح سري للتشفير (غيّره في الإنتاج الفعلي)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my-secret-key-123'
    
    # مسار قاعدة البيانات
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'data', 'database', 'sales.db')
    
    # إعدادات إضافية
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # رفع الملفات
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # حد أقصى 16 ميجابايت
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'raw')
    PROCESSED_FOLDER = os.path.join(BASE_DIR, 'data', 'processed')
    
    # إنشاء المجلدات إذا لم تكن موجودة
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)