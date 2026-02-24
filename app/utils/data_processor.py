import pandas as pd
import os
from datetime import datetime
from app import db
from app.models import Sale, Product
import numpy as np

class DataProcessor:
    """فئة معالجة بيانات المبيعات"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.df = None
        self.errors = []
        self.warnings = []
    
    def load_file(self, file_path):
        """
        قراءة ملف Excel أو CSV
        """
        try:
            # التأكد من وجود الملف
            if not os.path.exists(file_path):
                self.errors.append(f"الملف غير موجود: {file_path}")
                return False
            
            # تحديد نوع الملف من الامتداد
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.csv':
                self.df = pd.read_csv(file_path)
                print(f"✅ تم قراءة ملف CSV: {file_path}")
            elif file_extension in ['.xlsx', '.xls']:
                self.df = pd.read_excel(file_path)
                print(f"✅ تم قراءة ملف Excel: {file_path}")
            else:
                self.errors.append(f"نوع الملف غير مدعوم: {file_extension}")
                return False
            
            print(f"📊 عدد الصفوف: {len(self.df)}")
            print(f"📋 الأعمدة: {list(self.df.columns)}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"خطأ في قراءة الملف: {str(e)}")
            return False
    
    def validate_columns(self, required_columns):
        """
        التحقق من وجود الأعمدة المطلوبة
        """
        missing_columns = []
        for col in required_columns:
            if col not in self.df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            self.errors.append(f"الأعمدة المفقودة: {missing_columns}")
            return False
        
        print("✅ جميع الأعمدة المطلوبة موجودة")
        return True
    
    def clean_data(self):
        """
        تنظيف البيانات من القيم الفارغة والخاطئة
        """
        if self.df is None:
            self.errors.append("لا توجد بيانات للتنظيف")
            return False
        
        original_rows = len(self.df)
        
        # 1. إزالة الصفوف الفارغة تماماً
        self.df = self.df.dropna(how='all')
        
        # 2. معالجة القيم الفارغة في الأعمدة المهمة
        for col in ['product_name', 'quantity', 'price', 'sale_date']:
            if col in self.df.columns:
                if col in ['quantity', 'price']:
                    # للأعمدة الرقمية: املأ بالقيم الافتراضية
                    self.df[col] = self.df[col].fillna(0)
                elif col == 'product_name':
                    # للمنتجات: املأ بـ "منتج غير معروف"
                    self.df[col] = self.df[col].fillna('منتج غير معروف')
                elif col == 'sale_date':
                    # للتواريخ: املأ بالتاريخ الحالي
                    self.df[col] = self.df[col].fillna(datetime.now().strftime('%Y-%m-%d'))
        
        # 3. إزالة الصفوف المكررة
        if 'sale_id' in self.df.columns:
            self.df = self.df.drop_duplicates(subset=['sale_id'], keep='first')
        else:
            self.df = self.df.drop_duplicates()
        
        # 4. تنظيف البيانات الرقمية
        if 'quantity' in self.df.columns:
            # التأكد أن الكمية رقم صحيح وموجب
            self.df['quantity'] = pd.to_numeric(self.df['quantity'], errors='coerce').fillna(0).astype(int)
            self.df['quantity'] = self.df['quantity'].abs()  # قيمة مطلقة (موجبة)
        
        if 'price' in self.df.columns:
            # التأكد أن السعر رقم
            self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce').fillna(0)
            self.df['price'] = self.df['price'].abs()  # قيمة مطلقة
        
        # 5. تنظيف التواريخ
        if 'sale_date' in self.df.columns:
            try:
                self.df['sale_date'] = pd.to_datetime(self.df['sale_date'], errors='coerce')
                # إزالة التواريخ الفارغة بعد التحويل
                self.df.dropna(subset=['sale_date'], inplace=True)
            except:
                self.warnings.append("تحذير: مشكلة في تحويل التواريخ")
        
        cleaned_rows = len(self.df)
        removed_rows = original_rows - cleaned_rows
        
        if removed_rows > 0:
            self.warnings.append(f"تم إزالة {removed_rows} صفوف غير صالحة")
        
        print(f"✅ تم تنظيف البيانات: {cleaned_rows} صف صالح")
        return True
    
    def calculate_total_price(self):
        """
        حساب السعر الإجمالي إذا لم يكن موجوداً
        """
        if 'total_price' not in self.df.columns:
            if 'quantity' in self.df.columns and 'price' in self.df.columns:
                self.df['total_price'] = self.df['quantity'] * self.df['price']
                print("✅ تم حساب السعر الإجمالي")
    
    def extract_products(self):
        """
        استخراج قائمة المنتجات الفريدة
        """
        if 'product_name' not in self.df.columns:
            self.errors.append("لا يوجد عمود لأسماء المنتجات")
            return []
        
        unique_products = self.df['product_name'].unique()
        products_list = []
        
        for product_name in unique_products:
            # البحث عن سعر المنتج (أول سعر ظهر له)
            product_data = self.df[self.df['product_name'] == product_name].iloc[0]
            
            product = {
                'name': product_name,
                'category': product_data.get('category', 'عام'),
                'price': float(product_data.get('price', 0))
            }
            products_list.append(product)
        
        print(f"✅ تم استخراج {len(products_list)} منتج فريد")
        return products_list
    
    def save_to_database(self):
        """
        حفظ البيانات في قاعدة البيانات
        """
        if self.df is None or len(self.df) == 0:
            self.errors.append("لا توجد بيانات للحفظ")
            return False
        
        try:
            # 1. أولاً: حفظ أو تحديث المنتجات
            products = self.extract_products()
            product_map = {}  # لربط اسم المنتج بـ ID الخاص به
            
            for prod_data in products:
                # البحث عن المنتج في قاعدة البيانات
                product = Product.query.filter_by(name=prod_data['name']).first()
                
                if not product:
                    # إذا لم يكن موجوداً، أنشئ منتجاً جديداً
                    product = Product(
                        name=prod_data['name'],
                        category=prod_data['category'],
                        selling_price=prod_data['price']
                    )
                    db.session.add(product)
                    db.session.flush()  # للحصول على ID المنتج
                
                product_map[prod_data['name']] = product.id
            
            # 2. ثانياً: حفظ المبيعات
            sales_count = 0
            for _, row in self.df.iterrows():
                # التأكد من وجود المنتج في الخريطة
                product_name = row.get('product_name', 'منتج غير معروف')
                if product_name not in product_map:
                    continue
                
                # إنشاء كائن بيع جديد
                sale = Sale(
                    quantity=int(row.get('quantity', 0)),
                    total_price=float(row.get('total_price', row.get('quantity', 0) * row.get('price', 0))),
                    sale_date=row.get('sale_date', datetime.now()),
                    product_id=product_map[product_name],
                    user_id=self.user_id
                )
                db.session.add(sale)
                sales_count += 1
            
            # حفظ جميع التغييرات
            db.session.commit()
            print(f"✅ تم حفظ {sales_count} عملية بيع في قاعدة البيانات")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.errors.append(f"خطأ في حفظ البيانات: {str(e)}")
            return False
    
    def get_summary_stats(self):
        """
        الحصول على إحصائيات موجزة عن البيانات
        """
        if self.df is None:
            return {}
        
        stats = {
            'total_rows': len(self.df),
            'total_quantity': int(self.df['quantity'].sum()) if 'quantity' in self.df.columns else 0,
            'total_sales': float(self.df['total_price'].sum()) if 'total_price' in self.df.columns else 0,
            'avg_price': float(self.df['price'].mean()) if 'price' in self.df.columns else 0,
            'unique_products': self.df['product_name'].nunique() if 'product_name' in self.df.columns else 0,
            'date_range': None
        }
        
        if 'sale_date' in self.df.columns and len(self.df) > 0:
            stats['date_range'] = {
                'min': self.df['sale_date'].min(),
                'max': self.df['sale_date'].max()
            }
        
        return stats
    
    def process_file(self, file_path, required_columns=None):
        """
        الدالة الرئيسية: معالجة ملف كامل
        """
        print("🚀 بدء معالجة الملف...")
        
        # 1. قراءة الملف
        if not self.load_file(file_path):
            return False, self.errors, self.warnings, {}
        
        # 2. التحقق من الأعمدة المطلوبة
        if required_columns:
            default_columns = ['product_name', 'quantity', 'price', 'sale_date']
            cols_to_check = required_columns if required_columns else default_columns
            
            if not self.validate_columns(cols_to_check):
                return False, self.errors, self.warnings, {}
        
        # 3. تنظيف البيانات
        if not self.clean_data():
            return False, self.errors, self.warnings, {}
        
        # 4. حساب السعر الإجمالي
        self.calculate_total_price()
        
        # 5. حفظ في قاعدة البيانات
        if not self.save_to_database():
            return False, self.errors, self.warnings, {}
        
        # 6. الحصول على الإحصائيات
        stats = self.get_summary_stats()
        
        print("✅ تمت معالجة الملف بنجاح!")
        return True, self.errors, self.warnings, stats