from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os

# إنشاء الكائنات العالمية
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=None):
    """مصنع تطبيق Flask"""
    
    app = Flask(__name__)
    
    # تحميل الإعدادات
    if config_class is None:
        from config import Config
        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)
    
    # تهيئة الإضافات
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # استيراد النماذج لتسجيلها
    from app import models
    
    # إعدادات تسجيل الدخول
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'الرجاء تسجيل الدخول أولاً'
    login_manager.login_message_category = 'info'
    
    # تسجيل المسارات (Routes)
    from app.routes.auth import bp as auth_bp
    from app.routes.main import bp as main_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.upload import bp as  upload_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(upload_bp)
   
    # إنشاء جداول قاعدة البيانات
    with app.app_context():
        db.create_all()
    
    return app