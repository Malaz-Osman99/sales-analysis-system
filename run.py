import sys
import os

# أضف مسار المشروع إلى PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("✅ التطبيق يعمل على: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)