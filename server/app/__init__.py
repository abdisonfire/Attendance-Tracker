from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    
    # Initialize the database
    db.init_app(app)

    # Import and register the Blueprint
    from .routes import attendance_bp, login_manager
    app.register_blueprint(attendance_bp)
    login_manager.init_app(app)
    login_manager.login_view = "attendance.login"

    # Create the database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app
