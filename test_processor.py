from app.utils.data_processor import DataProcessor
from app import create_app, db
import pandas as pd
import os

# إنشاء تطبيق للسياق
app = create_app()

def create_test_file():
    """إنشاء ملف بيانات تجريبي"""
    test_data = {
        'product_name': ['منتج أ', 'منتج ب', 'منتج أ', 'منتج ج', 'منتج ب'],
        'quantity': [10, 5, 8, 12, 3],
        'price': [100, 200, 100, 150, 200],
        'sale_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        'category': ['إلكترونيات', 'ملابس', 'إلكترونيات', 'كتب', 'ملابس']
    }
    
    df = pd.DataFrame(test_data)
    test_file = 'test_sales.xlsx'
    df.to_excel(test_file, index=False)
    print(f"✅ تم إنشاء ملف تجريبي: {test_file}")
    return test_file

# تشغيل الاختبار
with app.app_context():
    print("=" * 50)
    print("🧪 بدء اختبار معالج البيانات")
    print("=" * 50)
    
    # 1. إنشاء ملف تجريبي
    test_file = create_test_file()
    
    # 2. معالجة الملف (باستخدام user_id = 1)
    processor = DataProcessor(user_id=1)
    success, errors, warnings, stats = processor.process_file(
        test_file, 
        required_columns=['product_name', 'quantity', 'price', 'sale_date']
    )
    
    # 3. عرض النتائج
    if success:
        print("\n✅✅✅ نجاح معالجة الملف! ✅✅✅")
        print("\n📊 الإحصائيات:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print("\n❌❌❌ فشل معالجة الملف ❌❌❌")
    
    if warnings:
        print("\n⚠️ التحذيرات:")
        for w in warnings:
            print(f"   - {w}")
    
    if errors:
        print("\n❌ الأخطاء:")
        for e in errors:
            print(f"   - {e}")
    
    # 4. تنظيف
    os.remove(test_file)
    print(f"\n🧹 تم حذف الملف التجريبي")