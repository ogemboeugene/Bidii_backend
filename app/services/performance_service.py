from app.models import GroupMonthlyPerformance, MonthlyPerformance
from app.extensions import db

class PerformanceService:
    @staticmethod
    def create_performance(data):
        performance = GroupMonthlyPerformance(**data)
        db.session.add(performance)
        db.session.commit()
        return performance
    
    @staticmethod
    def update_group_performance(performance, data):
        for key, value in data.items():
            if hasattr(performance, key):
                setattr(performance, key, value)
        db.session.commit()
        return performance
    
    @staticmethod
    def update_monthly_performance(performance, data):
        # Update fields in the performance object
        for field in data:
            if hasattr(performance, field):
                setattr(performance, field, data[field])
        db.session.commit()
        return performance

    @staticmethod
    def delete_group_performance(performance):
        db.session.delete(performance)
        db.session.commit()
    
    @staticmethod
    def delete_monthly_performance(performance):
        db.session.delete(performance)
        db.session.commit()
