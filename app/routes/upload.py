from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.data_processor import DataProcessor
from app import db
import os
from werkzeug.utils import secure_filename
from datetime import datetime

bp = Blueprint('upload', __name__)

# إعدادات رفع الملفات
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'file' not in request.files:
            flash('الرجاء اختيار ملف', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # إذا لم يختر المستخدم ملفاً
        if file.filename == '':
            flash('الرجاء اختيار ملف', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # تأمين اسم الملف
            filename = secure_filename(file.filename)
            
            # إنشاء اسم فريد للملف
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            # حفظ الملف مؤقتاً
            upload_folder = os.path.join('app', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            try:
                # معالجة الملف
                processor = DataProcessor(user_id=current_user.id)
                success, errors, warnings, stats = processor.process_file(
                    file_path,
                    required_columns=['product_name', 'quantity', 'price', 'sale_date']
                )
                
                if success:
                    flash('✅ تم رفع وتحليل الملف بنجاح!', 'success')
                    
                    # تخزين الإحصائيات في الجلسة لعرضها
                    from flask import session
                    session['last_upload_stats'] = stats
                    
                    return redirect(url_for('dashboard.show_dashboard'))
                else:
                    for error in errors:
                        flash(f'❌ {error}', 'error')
                    for warning in warnings:
                        flash(f'⚠️ {warning}', 'warning')
                    
            except Exception as e:
                flash(f'❌ حدث خطأ: {str(e)}', 'error')
            
            finally:
                # حذف الملف المؤقت
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        else:
            flash('❌ نوع الملف غير مدعوم. استخدم CSV أو Excel', 'error')
    
    return render_template('upload.html')