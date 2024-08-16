from flask import Flask
from flask_migrate import Migrate
from .extensions import db, ma, jwt, mail
from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)


    with app.app_context():
        from .routes import auth, transaction, performance, admin, notification, advance, history
        app.register_blueprint(auth.bp)
        app.register_blueprint(transaction.bp)
        app.register_blueprint(performance.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(notification.bp)
        app.register_blueprint(advance.bp)
        app.register_blueprint(history.bp)
    return app
