from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # التحقق من وجود المستخدم حسب البريد أو اسم المستخدم
    existing_email = User.query.filter_by(email='test@example.com').first()
    existing_username = User.query.filter_by(username='test_user').first()

    if existing_email or existing_username:
        print("✅ المستخدم التجريبي موجود بالفعل")
    else:
        # إنشاء مستخدم تجريبي
        user = User(
            username='test_user',
            email='test@example.com'
        )
        user.set_password('password123')
        
        db.session.add(user)
        try:
            db.session.commit()
            print("✅ تم إنشاء مستخدم تجريبي:")
            print("   البريد: test@example.com")
            print("   كلمة المرور: password123")
        except Exception as e:
            db.session.rollback()
            print(f"❌ فشل إنشاء المستخدم التجريبي: {e}")