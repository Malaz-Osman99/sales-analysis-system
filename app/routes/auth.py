from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm
from urllib.parse import urlparse

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    # إذا كان المستخدم مسجل بالفعل، حوله للوحة التحكم
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.show_dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # البحث عن المستخدم بالبريد الإلكتروني
        user = User.query.filter_by(email=form.email.data).first()
        
        # التحقق من وجود المستخدم وصحة كلمة المرور
        if user is None or not user.check_password(form.password.data):
            flash('❌ بريد إلكتروني أو كلمة مرور غير صحيحة', 'error')
            return redirect(url_for('auth.login'))
        
        # تسجيل الدخول
        login_user(user, remember=form.remember_me.data)
        
        # توجيه المستخدم للصفحة التي كان يحاول الوصول لها
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard.show_dashboard')
        
        flash(f'✅ مرحباً {user.username}! تم تسجيل الدخول بنجاح', 'success')
        return redirect(next_page)
    
    return render_template('login.html', title='تسجيل الدخول', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """صفحة تسجيل مستخدم جديد"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.show_dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # إنشاء مستخدم جديد
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        # حفظ في قاعدة البيانات
        db.session.add(user)
        db.session.commit()
        
        flash(f'✅ تم إنشاء الحساب بنجاح! مرحباً {user.username}', 'success')
        
        # تسجيل الدخول مباشرة بعد التسجيل
        login_user(user)
        return redirect(url_for('dashboard.show_dashboard'))
    
    return render_template('register.html', title='حساب جديد', form=form)

@bp.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('✅ تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required
def profile():
    """عرض الملف الشخصي"""
    return render_template('profile.html', title='الملف الشخصي')

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """تغيير كلمة المرور"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # التحقق من صحة كلمة المرور الحالية
        if not current_user.check_password(form.old_password.data):
            flash('❌ كلمة المرور الحالية غير صحيحة', 'error')
            return redirect(url_for('auth.change_password'))
        
        # تغيير كلمة المرور
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('✅ تم تغيير كلمة المرور بنجاح', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('change_password.html', title='تغيير كلمة المرور', form=form)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """تعديل الملف الشخصي"""
    if request.method == 'POST':
        # تحديث معلومات المستخدم
        current_user.username = request.form.get('username', current_user.username)
        # يمكن إضافة المزيد من الحقول هنا
        
        db.session.commit()
        flash('✅ تم تحديث الملف الشخصي', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('edit_profile.html', title='تعديل الملف الشخصي')