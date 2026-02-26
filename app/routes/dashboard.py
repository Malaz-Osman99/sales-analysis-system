from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__)

# Optional import of SalesPredictor (graceful fallback if sklearn not available)
try:
    from app.utils.predictor import SalesPredictor
    HAS_PREDICTOR = True
except ImportError:
    HAS_PREDICTOR = False

@bp.route('/dashboard')
@login_required
def show_dashboard():
    """عرض لوحة التحكم"""
    return render_template('dashboard.html', title='لوحة التحكم')

@bp.route('/predictions')
@login_required
def show_predictions():
    """عرض صفحة التنبؤات"""
    
    if not HAS_PREDICTOR:
        flash('ميزة التنبؤ غير متاحة. يرجى تثبيت scikit-learn.', 'warning')
        return render_template('predictions.html', has_data=False, error=True)
    
    predictor = SalesPredictor(user_id=current_user.id)
    results = predictor.full_prediction(days_ahead=30)
    
    if not results:
        flash('لا توجد بيانات كافية للتنبؤ. نحتاج على الأقل 30 يوم من البيانات.', 'warning')
        return render_template('predictions.html', has_data=False)
    
    # تجهيز بيانات الرسوم البيانية
    chart_data = {
        'labels': [p['date'] for p in results['predictions']],
        'sales': [p['predicted_sales'] for p in results['predictions']],
        'profit': [p['predicted_profit'] for p in results['predictions']],
        'lower': [p['confidence_lower'] for p in results['predictions']],
        'upper': [p['confidence_upper'] for p in results['predictions']]
    }
    
    return render_template(
        'predictions.html', 
        has_data=True,
        predictions=results['predictions'][:10],  # أول 10 أيام للعرض
        summary=results['summary'],
        chart_data=chart_data,
        model_type=results['model_type'],
        generated_at=results['generated_at']
    )