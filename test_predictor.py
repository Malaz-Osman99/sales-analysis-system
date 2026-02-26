from app.utils.predictor import SalesPredictor
from app import create_app, db
from app.models import User, Product, Sale
from datetime import datetime, timedelta
import random

app = create_app()

def create_test_data():
    """إنشاء بيانات تجريبية للاختبار"""
    
    with app.app_context():
        # إنشاء مستخدم تجريبي
        user = User.query.filter_by(username='test_user').first()
        if not user:
            user = User(username='test_user', email='test@test.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            print("✅ تم إنشاء مستخدم تجريبي")
        
        # إنشاء منتجات تجريبية
        products = []
        for i in range(5):
            product = Product(
                name=f'منتج {i+1}',
                category=random.choice(['إلكترونيات', 'ملابس', 'كتب']),
                selling_price=random.randint(50, 500)
            )
            db.session.add(product)
            products.append(product)
        
        db.session.commit()
        
        # إنشاء مبيعات تجريبية لآخر 200 يوم مع اتجاه تصاعدي
        base_sales = 1000
        for day in range(200):
            sale_date = datetime.now() - timedelta(days=200-day)
            
            # إضافة اتجاه (المبيعات تزيد مع الوقت)
            trend = day * 5
            
            # إضافة موسمية (نهاية الأسبوع مبيعات أعلى)
            weekday = sale_date.weekday()
            seasonal = 200 if weekday >= 5 else 0
            
            for _ in range(random.randint(5, 15)):
                product = random.choice(products)
                quantity = random.randint(1, 10)
                
                # سعر مع تقلبات عشوائية
                price = product.selling_price * quantity + random.randint(-20, 20)
                price = max(10, price)  # لا يقل عن 10
                
                sale = Sale(
                    quantity=quantity,
                    total_price=price,
                    sale_date=sale_date,
                    product_id=product.id,
                    user_id=user.id
                )
                db.session.add(sale)
        
        db.session.commit()
        print(f"✅ تم إنشاء مبيعات تجريبية لآخر 200 يوم")
        
        return user.id

with app.app_context():
    print("=" * 60)
    print("🧪 بدء اختبار نموذج التنبؤ")
    print("=" * 60)
    
    # 1. إنشاء بيانات تجريبية
    user_id = create_test_data()
    
    # 2. إنشاء متنبئ
    predictor = SalesPredictor(user_id=user_id)
    
    # 3. إجراء تنبؤ لـ 30 يوم
    results = predictor.full_prediction(days_ahead=30, model_type='linear')
    
    if results:
        print("\n📊 نتائج التنبؤ:")
        print("-" * 40)
        
        # الملخص
        print("\n📈 ملخص التنبؤ:")
        summary = results['summary']
        print(f"   الفترة: {summary['start_date']} إلى {summary['end_date']}")
        print(f"   إجمالي المبيعات المتوقعة: {summary['total_predicted_sales']:.2f} ريال")
        print(f"   متوسط المبيعات اليومية: {summary['avg_daily_sales']:.2f} ريال")
        
        if 'model_accuracy' in summary:
            print(f"\n🎯 دقة النموذج:")
            print(f"   R²: {summary['model_accuracy']['r2']:.3f}")
            print(f"   متوسط الخطأ: {summary['model_accuracy']['mae']:.2f} ريال")
        
        # عرض أول 5 تنبؤات
        print("\n📅 أول 5 أيام:")
        for i, pred in enumerate(results['predictions'][:5], 1):
            print(f"   يوم {i} ({pred['date']}): {pred['predicted_sales']:.0f} ريال (ربح: {pred['predicted_profit']:.0f} ريال)")
        
        # عرض آخر 5 تنبؤات
        print("\n📅 آخر 5 أيام:")
        for i, pred in enumerate(results['predictions'][-5:], 1):
            print(f"   يوم {i} ({pred['date']}): {pred['predicted_sales']:.0f} ريال (ربح: {pred['predicted_profit']:.0f} ريال)")
    
    print("\n" + "=" * 60)