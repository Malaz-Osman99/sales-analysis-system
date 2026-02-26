from app.utils.analyzer import SalesAnalyzer
from app import create_app, db
from app.models import User, Product, Sale
from datetime import datetime, timedelta
import random

app = create_app()

def create_test_data():
    """إنشاء بيانات تجريبية للاختبار"""
    
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
    for i in range(10):
        product = Product(
            name=f'منتج {i+1}',
            category=random.choice(['إلكترونيات', 'ملابس', 'كتب', 'أجهزة']),
            selling_price=random.randint(50, 500)
        )
        db.session.add(product)
        products.append(product)
    
    db.session.commit()
    
    # إنشاء مبيعات تجريبية لآخر 30 يوم
    for day in range(30):
        sale_date = datetime.now() - timedelta(days=day)
        for _ in range(random.randint(5, 20)):  # 5-20 عملية يومياً
            product = random.choice(products)
            quantity = random.randint(1, 10)
            price = product.selling_price * quantity
            
            sale = Sale(
                quantity=quantity,
                total_price=price,
                sale_date=sale_date,
                product_id=product.id,
                user_id=user.id
            )
            db.session.add(sale)
    
    db.session.commit()
    print(f"✅ تم إنشاء مبيعات تجريبية لآخر 30 يوم")
    
    return user.id

with app.app_context():
    print("=" * 60)
    print("🧪 بدء اختبار محلل المبيعات")
    print("=" * 60)
    
    # 1. إنشاء بيانات تجريبية
    user_id = create_test_data()
    
    # 2. إنشاء محلل
    analyzer = SalesAnalyzer(user_id=user_id)
    
    # 3. إجراء تحليل كامل
    results = analyzer.full_analysis()
    
    if results:
        print("\n📊 نتائج التحليل:")
        print("-" * 40)
        
        # مؤشرات الأداء
        print("\n📈 مؤشرات الأداء:")
        for key, value in results['kpis'].items():
            print(f"   {key}: {value:.2f}" if isinstance(value, float) else f"   {key}: {value}")
        
        # أفضل المنتجات
        print("\n🏆 أفضل 5 منتجات:")
        for i, p in enumerate(results['top_products'], 1):
            print(f"   {i}. {p['product_name']}: {p['total_sales']:.2f}")
        
        # الرؤى والتوصيات
        print("\n💡 الرؤى والتوصيات:")
        for insight in results['insights']:
            icon = {'positive': '✅', 'warning': '⚠️', 'negative': '📉', 'info': 'ℹ️'}
            print(f"   {icon.get(insight['type'], '•')} {insight['title']}")
            print(f"      {insight['message']}")
    
    print("\n" + "=" * 60)