from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import GroupMonthlyPerformance, MonthlyPerformance

class GroupMonthlyPerformanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = GroupMonthlyPerformance
        load_instance = True
        include_fk = True

class MonthlyPerformanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MonthlyPerformance
        load_instance = True
        include_fk = True
