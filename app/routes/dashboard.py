from flask import Blueprint, send_file, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.exporter import ReportExporter
from app.utils.analyzer import SalesAnalyzer
from app.utils.predictor import SalesPredictor
from datetime import datetime
import json
import io

bp = Blueprint('dashboard', __name__)

@bp.route('/export/<format>')
@login_required
def export_report(format):
    """تصدير التقرير بالصيغة المطلوبة"""
    
    # جمع البيانات للتصدير
    analyzer = SalesAnalyzer(user_id=current_user.id)
    results = analyzer.full_analysis()
    
    if not results:
        flash('لا توجد بيانات للتصدير', 'warning')
        return redirect(url_for('dashboard.show_dashboard'))
    
    # إضافة التنبؤات
    predictor = SalesPredictor(user_id=current_user.id)
    predictions = predictor.full_prediction(days_ahead=30)
    if predictions:
        results['predictions'] = predictions['predictions']
    
    # إنشاء المُصدر
    exporter = ReportExporter(user_name=current_user.username)
    
    # التصدير حسب الصيغة المطلوبة
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format == 'excel':
        excel_data = exporter.export_to_excel(results)
        return send_file(
            io.BytesIO(excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'sales_report_{timestamp}.xlsx'
        )
    
    elif format == 'pdf':
        pdf_data = exporter.export_to_pdf(results)
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'sales_report_{timestamp}.pdf'
        )
    
    elif format == 'csv':
        csv_data = exporter.export_to_csv(results)
        return send_file(
            io.BytesIO(csv_data),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sales_data_{timestamp}.csv'
        )
    
    else:
        flash('صيغة غير مدعومة', 'error')
        return redirect(url_for('dashboard.show_dashboard'))

@bp.route('/export/predictions/<format>')
@login_required
def export_predictions(format):
    """تصدير التنبؤات فقط"""
    
    predictor = SalesPredictor(user_id=current_user.id)
    results = predictor.full_prediction(days_ahead=30)
    
    if not results:
        flash('لا توجد تنبؤات للتصدير', 'warning')
        return redirect(url_for('dashboard.show_predictions'))
    
    exporter = ReportExporter(user_name=current_user.username)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format == 'excel':
        excel_data = exporter.export_to_excel({'predictions': results['predictions']})
        return send_file(
            io.BytesIO(excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'predictions_{timestamp}.xlsx'
        )
    
    elif format == 'csv':
        csv_data = exporter.export_to_csv({'predictions': results['predictions']}, data_type='predictions')
        return send_file(
            io.BytesIO(csv_data),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'predictions_{timestamp}.csv'
        )
    
    else:
        flash('صيغة غير مدعومة', 'error')
        return redirect(url_for('dashboard.show_predictions'))

@bp.route('/api/export/data')
@login_required
def get_export_data():
    """API لجلب بيانات التصدير (للاستخدام مع JavaScript)"""
    
    data_type = request.args.get('type', 'full')
    
    if data_type == 'predictions':
        predictor = SalesPredictor(user_id=current_user.id)
        results = predictor.full_prediction(days_ahead=30)
    else:
        analyzer = SalesAnalyzer(user_id=current_user.id)
        results = analyzer.full_analysis()
        
        # إضافة التنبؤات
        predictor = SalesPredictor(user_id=current_user.id)
        predictions = predictor.full_prediction(days_ahead=30)
        if predictions:
            results['predictions'] = predictions['predictions']
    
    return jsonify(results)