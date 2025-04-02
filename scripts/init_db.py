import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from utils.database import reset_db

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        reset_db()
        print("Database has been reset and recreated!") 