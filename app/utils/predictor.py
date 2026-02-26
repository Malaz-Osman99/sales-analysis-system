import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from app.models import Sale, Prediction
from app import db
import warnings
warnings.filterwarnings('ignore')

class SalesPredictor:
    """فئة التنبؤ بالمبيعات المستقبلية"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.df = None
        self.model = None
        self.accuracy_metrics = {}
        self.feature_columns = ['day', 'month', 'year', 'dayofweek', 'quarter', 'dayofyear']
    
    def load_data(self, months_history=12):
        """
        تحميل بيانات المبيعات التاريخية للتدريب
        """
        try:
            # جلب مبيعات آخر X شهر
            cutoff_date = datetime.now() - timedelta(days=30 * months_history)
            
            sales = Sale.query.filter(
                Sale.user_id == self.user_id,
                Sale.sale_date >= cutoff_date
            ).order_by(Sale.sale_date).all()
            
            if len(sales) < 30:  # نحتاج على الأقل 30 عملية للتنبؤ
                print(f"⚠️ بيانات غير كافية للتنبؤ: {len(sales)} عملية فقط")
                return False
            
            # تحويل إلى DataFrame
            data = []
            for sale in sales:
                data.append({
                    'date': sale.sale_date,
                    'total_price': sale.total_price,
                    'quantity': sale.quantity,
                    'product_id': sale.product_id
                })
            
            self.df = pd.DataFrame(data)
            
            # تجميع المبيعات يومياً
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.daily_sales = self.df.groupby(self.df['date'].dt.date).agg({
                'total_price': 'sum',
                'quantity': 'sum',
                'product_id': 'count'
            }).reset_index()
            
            self.daily_sales.columns = ['date', 'daily_sales', 'daily_quantity', 'transaction_count']
            self.daily_sales['date'] = pd.to_datetime(self.daily_sales['date'])
            self.daily_sales = self.daily_sales.sort_values('date')
            
            print(f"✅ تم تحميل {len(self.daily_sales)} يوم من بيانات المبيعات")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات: {str(e)}")
            return False
    
    def prepare_features(self, data):
        """
        تحضير الميزات للتنبؤ (استخراج خصائص التاريخ)
        """
        df_features = data.copy()
        
        # استخراج خصائص التاريخ
        df_features['day'] = df_features['date'].dt.day
        df_features['month'] = df_features['date'].dt.month
        df_features['year'] = df_features['date'].dt.year
        df_features['dayofweek'] = df_features['date'].dt.dayofweek
        df_features['quarter'] = df_features['date'].dt.quarter
        df_features['dayofyear'] = df_features['date'].dt.dayofyear
        df_features['weekend'] = (df_features['dayofweek'] >= 5).astype(int)
        
        # إضافة ميزات موسمية
        df_features['month_sin'] = np.sin(2 * np.pi * df_features['month'] / 12)
        df_features['month_cos'] = np.cos(2 * np.pi * df_features['month'] / 12)
        df_features['day_sin'] = np.sin(2 * np.pi * df_features['dayofweek'] / 7)
        df_features['day_cos'] = np.cos(2 * np.pi * df_features['dayofweek'] / 7)
        
        return df_features
    
    def create_lag_features(self, data, lag_days=[1, 2, 3, 7, 14, 30]):
        """
        إنشاء ميزات التأخير (المبيعات في الأيام السابقة)
        """
        df_lag = data.copy()
        
        for lag in lag_days:
            df_lag[f'sales_lag_{lag}'] = df_lag['daily_sales'].shift(lag)
            df_lag[f'quantity_lag_{lag}'] = df_lag['daily_quantity'].shift(lag)
        
        # إضافة المتوسطات المتحركة
        df_lag['sales_ma_7'] = df_lag['daily_sales'].rolling(window=7, min_periods=1).mean()
        df_lag['sales_ma_30'] = df_lag['daily_sales'].rolling(window=30, min_periods=1).mean()
        
        # إضافة الاتجاه (الفرق عن اليوم السابق)
        df_lag['sales_trend'] = df_lag['daily_sales'].diff()
        
        return df_lag
    
    def train_linear_regression(self):
        """
        تدريب نموذج الانحدار الخطي للتنبؤ
        """
        if self.daily_sales is None or len(self.daily_sales) < 30:
            return None
        
        # تحضير الميزات
        df_features = self.prepare_features(self.daily_sales)
        df_features = self.create_lag_features(df_features)
        
        # إزالة القيم الفارغة
        df_features = df_features.dropna()
        
        if len(df_features) < 20:
            print("⚠️ بيانات غير كافية بعد تنظيف القيم الفارغة")
            return None
        
        # اختيار الميزات للتدريب
        feature_cols = [
            'day', 'month', 'year', 'dayofweek', 'quarter', 'dayofyear',
            'weekend', 'month_sin', 'month_cos', 'day_sin', 'day_cos',
            'sales_ma_7', 'sales_ma_30', 'sales_trend'
        ]
        
        # إضافة ميزات التأخير
        lag_cols = [col for col in df_features.columns if 'lag_' in col]
        feature_cols.extend(lag_cols)
        
        X = df_features[feature_cols]
        y_sales = df_features['daily_sales']
        y_quantity = df_features['daily_quantity']
        
        # تقسيم البيانات إلى تدريب واختبار
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_sales_train, y_sales_test = y_sales[:split_idx], y_sales[split_idx:]
        
        # تدريب نموذج للمبيعات
        sales_model = LinearRegression()
        sales_model.fit(X_train, y_sales_train)
        
        # تدريب نموذج للكميات
        quantity_model = LinearRegression()
        quantity_model.fit(X_train, y_quantity[:split_idx])
        
        # تقييم النماذج
        y_sales_pred = sales_model.predict(X_test)
        y_quantity_pred = quantity_model.predict(X_test)
        
        # حساب مقاييس الدقة
        self.accuracy_metrics = {
            'sales': {
                'mae': mean_absolute_error(y_sales_test, y_sales_pred),
                'mse': mean_squared_error(y_sales_test, y_sales_pred),
                'rmse': np.sqrt(mean_squared_error(y_sales_test, y_sales_pred)),
                'r2': r2_score(y_sales_test, y_sales_pred),
                'mape': np.mean(np.abs((y_sales_test - y_sales_pred) / y_sales_test)) * 100
            },
            'quantity': {
                'mae': mean_absolute_error(y_quantity[split_idx:], y_quantity_pred),
                'rmse': np.sqrt(mean_squared_error(y_quantity[split_idx:], y_quantity_pred))
            }
        }
        
        print(f"✅ دقة النموذج (R²): {self.accuracy_metrics['sales']['r2']:.3f}")
        print(f"✅ متوسط الخطأ المطلق: {self.accuracy_metrics['sales']['mae']:.2f} ريال")
        
        return {
            'sales_model': sales_model,
            'quantity_model': quantity_model,
            'feature_cols': feature_cols,
            'X_train': X_train,
            'X_test': X_test
        }
    
    def train_polynomial_regression(self, degree=2):
        """
        تدريب نموذج الانحدار متعدد الحدود
        """
        if self.daily_sales is None or len(self.daily_sales) < 30:
            return None
        
        # استخدام التاريخ كميزة بسيطة
        df_simple = self.daily_sales.copy()
        df_simple['day_num'] = range(len(df_simple))
        
        X = df_simple[['day_num']].values
        y = df_simple['daily_sales'].values
        
        # تحويل الميزات إلى كثيرات حدود
        poly = PolynomialFeatures(degree=degree)
        X_poly = poly.fit_transform(X)
        
        # تقسيم البيانات
        split_idx = int(len(X_poly) * 0.8)
        X_train, X_test = X_poly[:split_idx], X_poly[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # تدريب النموذج
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # تقييم
        y_pred = model.predict(X_test)
        
        accuracy = {
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred)
        }
        
        print(f"✅ دقة النموذج متعدد الحدود (R²): {accuracy['r2']:.3f}")
        
        return {
            'model': model,
            'poly': poly,
            'accuracy': accuracy
        }
    
    def predict_future(self, days_ahead=30, model_type='linear'):
        """
        التنبؤ بالمبيعات المستقبلية
        """
        if self.daily_sales is None or len(self.daily_sales) < 30:
            return None
        
        if model_type == 'linear':
            model_result = self.train_linear_regression()
            if not model_result:
                return None
            
            # إنبياء تواريخ مستقبلية
            last_date = self.daily_sales['date'].max()
            future_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]
            
            # تحضير ميزات التواريخ المستقبلية
            future_df = pd.DataFrame({'date': future_dates})
            future_df = self.prepare_features(future_df)
            
            # نحتاج آخر القيم لحساب ميزات التأخير
            last_values = self.daily_sales.tail(30).copy()
            
            predictions = []
            
            for i, date in enumerate(future_dates):
                # نسخة من الصف الحالي
                row = future_df.iloc[i:i+1].copy()
                
                # إضافة ميزات التأخير (باستخدام آخر القيم المعروفة)
                for lag in [1, 2, 3, 7, 14, 30]:
                    if i < lag:
                        # استخدام القيم التاريخية
                        lag_value = last_values.iloc[-lag]['daily_sales'] if len(last_values) >= lag else 0
                    else:
                        # استخدام القيم المتوقعة
                        lag_value = predictions[i-lag]['predicted_sales']
                    
                    row[f'sales_lag_{lag}'] = lag_value
                
                # إضافة المتوسطات المتحركة
                if i < 7:
                    # استخدام المتوسط من التاريخ
                    row['sales_ma_7'] = last_values['daily_sales'].tail(7).mean()
                else:
                    # استخدام المتوسط من التنبؤات
                    recent_preds = [p['predicted_sales'] for p in predictions[-7:]]
                    row['sales_ma_7'] = np.mean(recent_preds)
                
                if i < 30:
                    row['sales_ma_30'] = last_values['daily_sales'].tail(30).mean()
                else:
                    recent_preds = [p['predicted_sales'] for p in predictions[-30:]]
                    row['sales_ma_30'] = np.mean(recent_preds)
                
                # إضافة الاتجاه
                if i == 0:
                    row['sales_trend'] = last_values['daily_sales'].iloc[-1] - last_values['daily_sales'].iloc[-2]
                else:
                    row['sales_trend'] = predictions[i-1]['predicted_sales'] - predictions[i-2]['predicted_sales'] if i > 1 else 0
                
                # التأكد من وجود جميع الأعمدة المطلوبة
                for col in model_result['feature_cols']:
                    if col not in row.columns:
                        row[col] = 0
                
                # التنبؤ
                X_pred = row[model_result['feature_cols']]
                pred_sales = model_result['sales_model'].predict(X_pred)[0]
                pred_quantity = model_result['quantity_model'].predict(X_pred)[0]
                
                predictions.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'predicted_sales': max(0, pred_sales),  # لا يمكن أن تكون المبيعات سالبة
                    'predicted_quantity': max(0, int(pred_quantity)),
                    'confidence_lower': max(0, pred_sales - self.accuracy_metrics['sales']['mae']),
                    'confidence_upper': pred_sales + self.accuracy_metrics['sales']['mae']
                })
            
            return {
                'predictions': predictions,
                'accuracy': self.accuracy_metrics,
                'model_type': 'linear_regression'
            }
        
        else:
            # نموذج بسيط (متوسط متحرك + موسمية)
            return self.simple_prediction(days_ahead)
    
    def simple_prediction(self, days_ahead=30):
        """
        نموذج تنبؤ بسيط (للمقارنة أو كبديل)
        """
        if self.daily_sales is None or len(self.daily_sales) < 30:
            return None
        
        # حساب المتوسطات الموسمية
        last_date = self.daily_sales['date'].max()
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]
        
        # متوسط المبيعات لنفس اليوم من الأسبوع
        weekday_avg = self.daily_sales.groupby(self.daily_sales['date'].dt.dayofweek)['daily_sales'].mean()
        
        # المتوسط العام
        overall_avg = self.daily_sales['daily_sales'].mean()
        
        # الاتجاه العام (باستخدام الانحدار الخطي البسيط)
        days = np.array(range(len(self.daily_sales))).reshape(-1, 1)
        sales = self.daily_sales['daily_sales'].values
        
        trend_model = LinearRegression()
        trend_model.fit(days, sales)
        
        predictions = []
        
        for i, date in enumerate(future_dates):
            dayofweek = date.weekday()
            
            # المكون الموسمي (اليوم من الأسبوع)
            seasonal = weekday_avg.get(dayofweek, overall_avg)
            
            # المكون الاتجاهي
            trend = trend_model.predict([[len(self.daily_sales) + i]])[0]
            
            # المزيج
            pred_sales = (seasonal + trend) / 2
            
            # حساب الثقة (بساطة)
            std_dev = self.daily_sales['daily_sales'].std()
            
            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_sales': max(0, pred_sales),
                'predicted_quantity': max(0, int(pred_sales / overall_avg * self.daily_sales['daily_quantity'].mean())),
                'confidence_lower': max(0, pred_sales - std_dev),
                'confidence_upper': pred_sales + std_dev,
                'method': 'simple'
            })
        
        return {
            'predictions': predictions,
            'accuracy': {
                'note': 'نموذج بسيط يعتمد على الموسمية والاتجاه'
            },
            'model_type': 'simple_seasonal'
        }
    
    def predict_profit(self, predictions, profit_margin=0.3):
        """
        التنبؤ بالأرباح بناءً على توقعات المبيعات
        """
        profit_predictions = []
        
        for pred in predictions['predictions']:
            profit = pred['predicted_sales'] * profit_margin
            
            profit_predictions.append({
                'date': pred['date'],
                'predicted_sales': pred['predicted_sales'],
                'predicted_profit': profit,
                'profit_margin': profit_margin * 100,
                'confidence_lower': pred['confidence_lower'] * profit_margin,
                'confidence_upper': pred['confidence_upper'] * profit_margin
            })
        
        total_sales = sum(p['predicted_sales'] for p in profit_predictions)
        total_profit = sum(p['predicted_profit'] for p in profit_predictions)
        
        return {
            'daily': profit_predictions,
            'total_sales': total_sales,
            'total_profit': total_profit,
            'avg_daily_sales': total_sales / len(profit_predictions),
            'avg_daily_profit': total_profit / len(profit_predictions)
        }
    
    def save_predictions(self, predictions, period_days=30):
        """
        حفظ التنبؤات في قاعدة البيانات
        """
        try:
            # حذف التنبؤات القديمة لهذا المستخدم
            Prediction.query.filter_by(user_id=self.user_id).delete()
            
            # حفظ التنبؤات الجديدة
            for pred in predictions['predictions'][:period_days]:
                prediction = Prediction(
                    predicted_sales=pred['predicted_sales'],
                    predicted_profit=pred.get('predicted_profit', pred['predicted_sales'] * 0.3),
                    prediction_period=pred['date'],
                    user_id=self.user_id
                )
                db.session.add(prediction)
            
            db.session.commit()
            print(f"✅ تم حفظ {len(predictions['predictions'][:period_days])} تنبؤ في قاعدة البيانات")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في حفظ التنبؤات: {str(e)}")
    
    def get_prediction_summary(self, predictions):
        """
        الحصول على ملخص التنبؤات
        """
        if not predictions or 'predictions' not in predictions:
            return {}
        
        pred_list = predictions['predictions']
        
        summary = {
            'total_predicted_sales': sum(p['predicted_sales'] for p in pred_list),
            'avg_daily_sales': np.mean([p['predicted_sales'] for p in pred_list]),
            'max_predicted_sales': max(pred_list, key=lambda x: x['predicted_sales']),
            'min_predicted_sales': min(pred_list, key=lambda x: x['predicted_sales']),
            'total_days': len(pred_list),
            'start_date': pred_list[0]['date'],
            'end_date': pred_list[-1]['date'],
            'confidence_level': 'متوسط' if predictions.get('accuracy') else 'تقديري'
        }
        
        # إضافة معلومات الدقة إن وجدت
        if 'accuracy' in predictions and predictions['accuracy']:
            if 'sales' in predictions['accuracy']:
                summary['model_accuracy'] = {
                    'r2': predictions['accuracy']['sales']['r2'],
                    'mae': predictions['accuracy']['sales']['mae']
                }
        
        return summary
    
    def full_prediction(self, days_ahead=30, model_type='linear'):
        """
        إجراء تنبؤ كامل
        """
        print(f"🚀 بدء التنبؤ للمدة {days_ahead} يوماً قادمة...")
        
        # 1. تحميل البيانات
        if not self.load_data():
            return None
        
        # 2. إجراء التنبؤ
        predictions = self.predict_future(days_ahead, model_type)
        
        if not predictions:
            return None
        
        # 3. التنبؤ بالأرباح
        profit_predictions = self.predict_profit(predictions)
        
        # 4. حفظ التنبؤات
        self.save_predictions(profit_predictions, days_ahead)
        
        # 5. إعداد الملخص
        summary = self.get_prediction_summary(profit_predictions)
        
        result = {
            'predictions': profit_predictions['daily'],
            'summary': summary,
            'model_type': predictions['model_type'],
            'accuracy': predictions.get('accuracy'),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        print("✅✅✅ اكتمل التنبؤ بنجاح! ✅✅✅")
        return result