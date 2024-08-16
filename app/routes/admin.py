from flask import Blueprint, request, jsonify
from app.models import AdminLog
from app.extensions import db
from app.schemas import AdminLogSchema
from app.services.admin_service import AdminService
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('admin', __name__)

@bp.route('/admin/logs', methods=['POST'])
@jwt_required()
def create_admin_log():
    data = request.get_json()
    schema = AdminLogSchema()

    try:
        # Validate and deserialize input data
        admin_log = schema.load(data, session=db.session)
        db.session.add(admin_log)
        db.session.commit()
        return schema.dump(admin_log), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@bp.route('/admin/logs', methods=['GET'])
@jwt_required()
def get_admin_logs():
    try:
        logs = AdminLog.query.all()
        return jsonify(AdminLogSchema(many=True).dump(logs)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
