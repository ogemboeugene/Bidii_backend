from flask import Flask
from flask_cors import CORS
from . import auth, transaction, performance, admin, notification, advance, history

app = Flask(__name__)
CORS(app)
def register_blueprints(app):
    app.register_blueprint(auth.bp)
    app.register_blueprint(transaction.bp)
    app.register_blueprint(performance.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(notification.bp)
    app.register_blueprint(advance.bp)
    app.register_blueprint(history.bp)