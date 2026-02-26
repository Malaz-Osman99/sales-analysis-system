import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.models import Sale, Product, Analysis
from app import db
from sqlalchemy import func, extract
import calendar

class SalesAnalyzer:
    """فئة تحليل المبيعات واستخراج المؤشرات"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.df = None
        self.insights = []
    
    def load_data_from_db(self, start_date=None, end_date=None):
        """
        تحميل بيانات المبيعات من قاعدة البيانات
        """
        try:
            # استعلام المبيعات للمستخدم الحالي
            query = Sale.query.filter_by(user_id=self.user_id)
            
            # تطبيق فلترة التاريخ إذا وجدت
            if start_date:
                query = query.filter(Sale.sale_date >= start_date)
            if end_date:
                query = filter(Sale.sale_date <= end_date)
            
            sales = query.all()
            
            if not sales:
                print("⚠️ لا توجد مبيعات لهذا المستخدم")
                return False
            
            # تحويل إلى DataFrame للتحليل
            data = []
            for sale in sales:
                data.append({
                    'sale_id': sale.id,
                    'product_id': sale.product_id,
                    'product_name': sale.product.name if sale.product else 'غير معروف',
                    'product_category': sale.product.category if sale.product else 'عام',
                    'quantity': sale.quantity,
                    'total_price': sale.total_price,
                    'sale_date': sale.sale_date,
                    'unit_price': sale.total_price / sale.quantity if sale.quantity > 0 else 0
                })
            
            self.df = pd.DataFrame(data)
            print(f"✅ تم تحميل {len(self.df)} عملية بيع")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات: {str(e)}")
            return False
    
    def calculate_kpis(self):
        """
        حساب مؤشرات الأداء الرئيسية
        """
        if self.df is None or len(self.df) == 0:
            return {}
        
        kpis = {}
        
        # 1. إجمالي المبيعات
        kpis['total_sales'] = float(self.df['total_price'].sum())
        
        # 2. إجمالي عدد العمليات
        kpis['total_transactions'] = len(self.df)
        
        # 3. متوسط قيمة العملية
        kpis['avg_transaction_value'] = float(self.df['total_price'].mean())
        
        # 4. إجمالي الكميات المباعة
        kpis['total_quantity'] = int(self.df['quantity'].sum())
        
        # 5. متوسط الكمية لكل عملية
        kpis['avg_quantity'] = float(self.df['quantity'].mean())
        
        # 6. أعلى عملية بيع
        kpis['max_sale'] = float(self.df['total_price'].max())
        
        # 7. أقل عملية بيع
        kpis['min_sale'] = float(self.df['total_price'].min())
        
        # 8. عدد المنتجات الفريدة
        kpis['unique_products'] = self.df['product_name'].nunique()
        
        print("✅ تم حساب مؤشرات الأداء")
        return kpis
    
    def top_products(self, n=5, by='total_price'):
        """
        أفضل المنتجات أداءً
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # تجميع المبيعات حسب المنتج
        product_stats = self.df.groupby(['product_id', 'product_name', 'product_category']).agg({
            'total_price': 'sum',
            'quantity': 'sum',
            'sale_id': 'count'
        }).reset_index()
        
        # إعادة تسمية الأعمدة
        product_stats.columns = ['product_id', 'product_name', 'category', 
                                 'total_sales', 'total_quantity', 'transaction_count']
        
        # حساب متوسط السعر
        product_stats['avg_price'] = product_stats['total_sales'] / product_stats['total_quantity']
        
        # ترتيب حسب المعيار المطلوب
        if by == 'total_price':
            product_stats = product_stats.sort_values('total_sales', ascending=False)
        elif by == 'quantity':
            product_stats = product_stats.sort_values('total_quantity', ascending=False)
        elif by == 'transactions':
            product_stats = product_stats.sort_values('transaction_count', ascending=False)
        
        top_n = product_stats.head(n).to_dict('records')
        
        print(f"✅ تم استخراج أفضل {n} منتج")
        return top_n
    
    def bottom_products(self, n=5):
        """
        أسوأ المنتجات أداءً (الأقل مبيعاً)
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # تجميع المبيعات حسب المنتج
        product_stats = self.df.groupby(['product_id', 'product_name', 'product_category']).agg({
            'total_price': 'sum',
            'quantity': 'sum',
            'sale_id': 'count'
        }).reset_index()
        
        product_stats.columns = ['product_id', 'product_name', 'category', 
                                 'total_sales', 'total_quantity', 'transaction_count']
        
        # ترتيب تصاعدي (الأقل أولاً)
        product_stats = product_stats.sort_values('total_sales', ascending=True)
        
        bottom_n = product_stats.head(n).to_dict('records')
        
        print(f"✅ تم استخراج أسوأ {n} منتج")
        return bottom_n
    
    def sales_over_time(self, period='daily'):
        """
        تحليل المبيعات عبر الزمن
        """
        if self.df is None or len(self.df) == 0:
            return {}
        
        # نسخة من البيانات مع عمود التاريخ
        df_time = self.df.copy()
        df_time['date'] = pd.to_datetime(df_time['sale_date'])
        
        if period == 'daily':
            # تجميع يومي
            time_series = df_time.groupby(df_time['date'].dt.date).agg({
                'total_price': 'sum',
                'quantity': 'sum',
                'sale_id': 'count'
            }).reset_index()
            # Normalize column names
            time_series.columns = ['date', 'total_sales', 'total_quantity', 'transaction_count']
            # Add label for consistency
            time_series['label'] = time_series['date'].apply(lambda d: pd.to_datetime(d).strftime('%Y-%m-%d'))
            
        elif period == 'weekly':
            # تجميع أسبوعي
            df_time['week'] = df_time['date'].dt.isocalendar().week
            df_time['year'] = df_time['date'].dt.year
            time_series = df_time.groupby(['year', 'week']).agg({
                'total_price': 'sum',
                'quantity': 'sum',
                'sale_id': 'count'
            }).reset_index()
            
            # Normalize column names
            time_series.columns = ['year', 'week', 'total_sales', 'total_quantity', 'transaction_count']
            time_series['label'] = time_series.apply(
                lambda x: f"الأسبوع {x['week']}, {x['year']}", axis=1
            )
            
        elif period == 'monthly':
            # تجميع شهري
            df_time['month'] = df_time['date'].dt.month
            df_time['year'] = df_time['date'].dt.year
            df_time['month_name'] = df_time['date'].dt.month_name()
            
            time_series = df_time.groupby(['year', 'month', 'month_name']).agg({
                'total_price': 'sum',
                'quantity': 'sum',
                'sale_id': 'count'
            }).reset_index()
            # Normalize column names
            time_series.columns = ['year', 'month', 'month_name', 'total_sales', 'total_quantity', 'transaction_count']
            
            # ترتيب حسب التاريخ
            time_series = time_series.sort_values(['year', 'month'])
            
            # إنشاء تسمية للشهر
            time_series['label'] = time_series.apply(
                lambda x: f"{x['month_name']} {x['year']}", axis=1
            )
        
        elif period == 'yearly':
            # تجميع سنوي
            df_time['year'] = df_time['date'].dt.year
            time_series = df_time.groupby('year').agg({
                'total_price': 'sum',
                'quantity': 'sum',
                'sale_id': 'count'
            }).reset_index()
            # Normalize column names
            time_series.columns = ['year', 'total_sales', 'total_quantity', 'transaction_count']
            time_series['label'] = time_series['year'].astype(str)
        
        print(f"✅ تم تحليل المبيعات {period}")
        # Ensure all records contain 'total_sales' key even if some branches differed
        return time_series.to_dict('records')
    
    def category_analysis(self):
        """
        تحليل المبيعات حسب الفئة
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        category_stats = self.df.groupby('product_category').agg({
            'total_price': 'sum',
            'quantity': 'sum',
            'product_id': 'nunique',
            'sale_id': 'count'
        }).reset_index()
        
        category_stats.columns = ['category', 'total_sales', 'total_quantity', 
                                  'unique_products', 'transaction_count']
        
        # حساب النسبة المئوية
        total_sales = category_stats['total_sales'].sum()
        if total_sales > 0:
            category_stats['percentage'] = (category_stats['total_sales'] / total_sales * 100).round(2)
        
        category_stats = category_stats.sort_values('total_sales', ascending=False)
        
        print("✅ تم تحليل المبيعات حسب الفئة")
        return category_stats.to_dict('records')
    
    def peak_hours_analysis(self):
        """
        تحليل أوقات الذروة (ساعات اليوم)
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # استخراج الساعة من التاريخ
        df_hours = self.df.copy()
        df_hours['hour'] = pd.to_datetime(df_hours['sale_date']).dt.hour
        
        hour_stats = df_hours.groupby('hour').agg({
            'total_price': 'sum',
            'sale_id': 'count'
        }).reset_index()
        
        hour_stats.columns = ['hour', 'total_sales', 'transaction_count']
        
        # ترتيب حسب الساعة
        hour_stats = hour_stats.sort_values('hour')
        
        # إضافة تسميات للساعات
        hour_stats['label'] = hour_stats['hour'].apply(
            lambda x: f"{x:02d}:00 - {x+1:02d}:00"
        )
        
        print("✅ تم تحليل أوقات الذروة")
        return hour_stats.to_dict('records')
    
    def weekday_analysis(self):
        """
        تحليل المبيعات حسب أيام الأسبوع
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        # استخراج يوم الأسبوع
        df_weekday = self.df.copy()
        df_weekday['weekday'] = pd.to_datetime(df_weekday['sale_date']).dt.weekday
        df_weekday['weekday_name'] = pd.to_datetime(df_weekday['sale_date']).dt.day_name()
        
        # الأيام بالعربية
        arabic_days = {
            'Monday': 'الاثنين',
            'Tuesday': 'الثلاثاء', 
            'Wednesday': 'الأربعاء',
            'Thursday': 'الخميس',
            'Friday': 'الجمعة',
            'Saturday': 'السبت',
            'Sunday': 'الأحد'
        }
        
        weekday_stats = df_weekday.groupby(['weekday', 'weekday_name']).agg({
            'total_price': 'sum',
            'sale_id': 'count'
        }).reset_index()
        
        weekday_stats.columns = ['weekday_num', 'weekday_en', 'total_sales', 'transaction_count']
        
        # إضافة الاسم العربي
        weekday_stats['weekday_ar'] = weekday_stats['weekday_en'].map(arabic_days)
        
        # ترتيب حسب اليوم
        weekday_stats = weekday_stats.sort_values('weekday_num')
        
        print("✅ تم تحليل المبيعات حسب أيام الأسبوع")
        return weekday_stats.to_dict('records')
    
    def profit_analysis(self, cost_data=None):
        """
        تحليل الأرباح (إذا توفرت بيانات التكلفة)
        """
        if self.df is None or len(self.df) == 0:
            return {}
        
        # إذا لم تكن بيانات التكلفة متوفرة، استخدم تقدير (هامش ربح 30%)
        if cost_data is None:
            # تقدير التكلفة كـ 70% من سعر البيع
            estimated_cost = self.df['total_price'].sum() * 0.7
            estimated_profit = self.df['total_price'].sum() * 0.3
            profit_margin = 30.0
            
            return {
                'total_revenue': float(self.df['total_price'].sum()),
                'estimated_cost': float(estimated_cost),
                'estimated_profit': float(estimated_profit),
                'profit_margin': profit_margin,
                'note': 'تقديري (هامش ربح 30%)'
            }
        
        # هنا يمكن إضافة منطق حساب الأرباح الفعلية إذا توفرت بيانات التكلفة
        return {}
    
    def generate_insights(self):
        """
        توليد رؤى وتوصيات بناءً على التحليل
        """
        insights = []
        
        if self.df is None or len(self.df) == 0:
            return insights
        
        # 1. أفضل منتج
        top = self.top_products(1)
        if top:
            insights.append({
                'type': 'positive',
                'title': '🌟 أفضل منتج',
                'message': f"منتج {top[0]['product_name']} هو الأكثر مبيعاً بإجمالي {top[0]['total_sales']:.2f}"
            })
        
        # 2. أسوأ منتج
        bottom = self.bottom_products(1)
        if bottom and bottom[0]['total_sales'] > 0:
            insights.append({
                'type': 'warning',
                'title': '⚠️ منتج يحتاج اهتمام',
                'message': f"منتج {bottom[0]['product_name']} مبيعاته منخفضة ({bottom[0]['total_sales']:.2f})"
            })
        
        # 3. أفضل يوم
        weekday = self.weekday_analysis()
        if weekday:
            best_day = max(weekday, key=lambda x: x['total_sales'])
            insights.append({
                'type': 'info',
                'title': '📅 أفضل يوم للمبيعات',
                'message': f"يوم {best_day['weekday_ar']} هو الأعلى مبيعاً"
            })
        
        # 4. أفضل ساعة
        hours = self.peak_hours_analysis()
        if hours:
            best_hour = max(hours, key=lambda x: x['total_sales'])
            insights.append({
                'type': 'info',
                'title': '⏰ أفضل وقت للبيع',
                'message': f"الساعة {best_hour['label']} هي ذروة المبيعات"
            })
        
        # 5. متوسط قيمة العملية
        kpis = self.calculate_kpis()
        if kpis and kpis['avg_transaction_value'] > 0:
            insights.append({
                'type': 'info',
                'title': '💰 متوسط قيمة العملية',
                'message': f"متوسط قيمة الفاتورة هو {kpis['avg_transaction_value']:.2f}"
            })
        
        # 6. تنبيه إذا كان هناك انخفاض
        time_series = self.sales_over_time('monthly')
        if len(time_series) >= 2:
            # helper to support both new key 'total_sales' and legacy 'total_price'
            def _get_total(entry):
                return float(entry.get('total_sales', entry.get('total_price', 0)) or 0)

            last_month = _get_total(time_series[-1])
            prev_month = _get_total(time_series[-2])

            if prev_month > 0:
                change = ((last_month - prev_month) / prev_month) * 100

                if change > 10:
                    insights.append({
                        'type': 'positive',
                        'title': '📈 نمو إيجابي',
                        'message': f"المبيعات ارتفعت {change:.1f}% مقارنة بالشهر الماضي"
                    })
                elif change < -10:
                    insights.append({
                        'type': 'negative',
                        'title': '📉 انخفاض في المبيعات',
                        'message': f"المبيعات انخفضت {abs(change):.1f}% مقارنة بالشهر الماضي"
                    })
        
        print(f"✅ تم توليد {len(insights)} رؤية")
        return insights
    
    def save_analysis(self):
        """
        حفظ نتائج التحليل في قاعدة البيانات
        """
        try:
            kpis = self.calculate_kpis()
            top = self.top_products(1)
            bottom = self.bottom_products(1)
            
            analysis = Analysis(
                total_sales=kpis.get('total_sales', 0),
                total_profit=kpis.get('estimated_profit', 0),
                best_product=top[0]['product_name'] if top else '',
                worst_product=bottom[0]['product_name'] if bottom else '',
                user_id=self.user_id
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            print("✅ تم حفظ التحليل في قاعدة البيانات")
            return analysis.id
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في حفظ التحليل: {str(e)}")
            return None
    
    def full_analysis(self, start_date=None, end_date=None):
        """
        إجراء تحليل كامل
        """
        print("🚀 بدء التحليل الشامل...")
        
        # 1. تحميل البيانات
        if not self.load_data_from_db(start_date, end_date):
            return None
        
        # 2. حساب المؤشرات
        kpis = self.calculate_kpis()
        
        # 3. أفضل المنتجات
        top_products = self.top_products(5)
        
        # 4. أسوأ المنتجات
        bottom_products = self.bottom_products(5)
        
        # 5. تحليل زمني
        daily_sales = self.sales_over_time('daily')
        monthly_sales = self.sales_over_time('monthly')
        
        # 6. تحليل الفئات
        categories = self.category_analysis()
        
        # 7. تحليل أوقات الذروة
        peak_hours = self.peak_hours_analysis()
        
        # 8. تحليل أيام الأسبوع
        weekdays = self.weekday_analysis()
        
        # 9. تحليل الأرباح (تقديري)
        profit = self.profit_analysis()
        
        # 10. توليد الرؤى
        insights = self.generate_insights()
        
        # 11. حفظ التحليل
        analysis_id = self.save_analysis()
        
        result = {
            'analysis_id': analysis_id,
            'analysis_date': datetime.now(),
            'kpis': kpis,
            'top_products': top_products,
            'bottom_products': bottom_products,
            'daily_sales': daily_sales,
            'monthly_sales': monthly_sales,
            'categories': categories,
            'peak_hours': peak_hours,
            'weekdays': weekdays,
            'profit_analysis': profit,
            'insights': insights
        }
        
        print("✅✅✅ اكتمل التحليل الشامل! ✅✅✅")
        return result