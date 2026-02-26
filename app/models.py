from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    """نموذج المستخدمين"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    sales = db.relationship('Sale', backref='user', lazy=True)
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    
    def set_password(self, password):
        """تشفير كلمة المرور"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    """نموذج المنتجات"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    cost_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)
    
    # العلاقات
    sales = db.relationship('Sale', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Sale(db.Model):
    """نموذج المبيعات"""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # المفاتيح الخارجية
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Sale {self.id} - {self.total_price}>'

class Analysis(db.Model):
    """نموذج التحليلات"""
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    total_sales = db.Column(db.Float)
    total_profit = db.Column(db.Float)
    best_product = db.Column(db.String(100))
    worst_product = db.Column(db.String(100))
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # المفاتيح الخارجية
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Analysis {self.id} - {self.analysis_date}>'

class Prediction(db.Model):
    """نموذج التنبؤات"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    predicted_sales = db.Column(db.Float)
    predicted_profit = db.Column(db.Float)
    prediction_period = db.Column(db.String(50))  # مثلاً: '2024-06'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # المفاتيح الخارجية
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Prediction {self.id} - {self.predicted_sales}>'