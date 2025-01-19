from . import db
from flask_login import UserMixin
class Attendance(db.Model):
    __tablename__ = "attendance"
    
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing ID
    name = db.Column(db.String(100), nullable=False)  # Employee name
    date = db.Column(db.Date, nullable=False)  # Date of attendance
    isPresent = db.Column(db.Boolean, nullable=False)  # True if present, False otherwise

class Holidays(db.Model):
    __tablename__ = "holidays"
    
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing ID
    date = db.Column(db.Date, nullable=False)  # Date of the holiday

class Users(db.Model, UserMixin):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing ID
    username = db.Column(db.String(255), unique=True, nullable=False)  # Unique username
    password = db.Column(db.String(255), nullable=False)  # Password hash