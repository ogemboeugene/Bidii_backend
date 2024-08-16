from app.models import AdminLog
from app.extensions import db

class AdminService:
    @staticmethod
    def create_log(data):
        # log = AdminLog(**data)
        log = AdminLog(action=data['action'], admin_id=data['admin_id'])
        db.session.add(log)
        db.session.commit()
        return log
