from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
ma = Marshmallow()
