import os
import shutil
from app import create_app

app = create_app(os.getenv('FLASK_CONFIG') or 'development')

def backup_db():
    with app.app_context():
        db_path = os.path.join(app.instance_path, 'app.db')
        backup_path = os.path.join(app.instance_path, 'app_backup.db')
        shutil.copyfile(db_path, backup_path)
        print('Database backup created successfully.')

if __name__ == '__main__':
    backup_db()
