import pytest
from app.models import Scam
from app.schemas import ScamSchema

@pytest.fixture
def scam_data():
    return {
        'user_id': 1,
        'description': 'Received phishing email attempting to steal credentials.'
    }

def test_scam_schema_load_instance(scam_data):
    schema = ScamSchema()
    scam_report = schema.load(scam_data)
    assert scam_report.user_id == scam_data['user_id']
    assert scam_report.description == scam_data['description']

def test_scam_schema_dump_instance(scam_data):
    scam_report = Scam(**scam_data)
    schema = ScamSchema()
    result = schema.dump(scam_report)
    assert result == scam_data
