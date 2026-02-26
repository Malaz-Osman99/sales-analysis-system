from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    """نموذج تسجيل الدخول"""
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='البريد الإلكتروني مطلوب'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='كلمة المرور مطلوبة')
    ])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class RegistrationForm(FlaskForm):
    """نموذج تسجيل مستخدم جديد"""
    username = StringField('اسم المستخدم', validators=[
        DataRequired(message='اسم المستخدم مطلوب'),
        Length(min=3, max=20, message='اسم المستخدم يجب أن يكون بين 3 و 20 حرف')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='البريد الإلكتروني مطلوب'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='كلمة المرور مطلوبة'),
        Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
    ])
    password2 = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(message='يرجى تأكيد كلمة المرور'),
        EqualTo('password', message='كلمتا المرور غير متطابقتين')
    ])
    submit = SubmitField('إنشاء حساب')
    
    def validate_username(self, username):
        """التحقق من عدم تكرار اسم المستخدم"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('اسم المستخدم موجود بالفعل. الرجاء اختيار اسم آخر.')
    
    def validate_email(self, email):
        """التحقق من عدم تكرار البريد الإلكتروني"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('البريد الإلكتروني مسجل بالفعل. الرجاء استخدام بريد آخر.')

class ChangePasswordForm(FlaskForm):
    """نموذج تغيير كلمة المرور"""
    old_password = PasswordField('كلمة المرور الحالية', validators=[
        DataRequired(message='كلمة المرور الحالية مطلوبة')
    ])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[
        DataRequired(message='كلمة المرور الجديدة مطلوبة'),
        Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', validators=[
        DataRequired(message='يرجى تأكيد كلمة المرور'),
        EqualTo('new_password', message='كلمتا المرور غير متطابقتين')
    ])
    submit = SubmitField('تغيير كلمة المرور')

class ResetPasswordRequestForm(FlaskForm):
    """نموذج طلب إعادة تعيين كلمة المرور"""
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='البريد الإلكتروني مطلوب'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    submit = SubmitField('إرسال رابط إعادة التعيين')

class ResetPasswordForm(FlaskForm):
    """نموذج إعادة تعيين كلمة المرور"""
    password = PasswordField('كلمة المرور الجديدة', validators=[
        DataRequired(message='كلمة المرور الجديدة مطلوبة'),
        Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
    ])
    password2 = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(message='يرجى تأكيد كلمة المرور'),
        EqualTo('password', message='كلمتا المرور غير متطابقتين')
    ])
    submit = SubmitField('تغيير كلمة المرور')