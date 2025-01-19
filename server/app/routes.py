from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from . import db
from .models import Attendance, Holidays, Users
from datetime import datetime
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import bcrypt

# Create a Blueprint for routes
attendance_bp = Blueprint("attendance", __name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Create a form for the login page
class LoginForm(FlaskForm):
    username = StringField("Username", [DataRequired()])
    password = PasswordField("Password", [DataRequired()])
    submit = SubmitField("Login")

# Helper function to check if today is a holiday
def is_holiday():
    today = datetime.now().date()
    first = Holidays.query.filter_by(date=today).first() is not None # Check if today is a special holiday
    second = today.weekday() == 4 or today.weekday() == 5 # Friday or Saturday
    return first or second

@attendance_bp.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("attendance.dashboard"))
    return redirect(url_for("attendance.login"))

# Login page
@attendance_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("attendance.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user and bcrypt.checkpw(form.password.data.encode("utf-8"), user.password):
            login_user(user)
            return redirect(url_for("attendance.dashboard"))
    return render_template("login.html", login_form=form)


@attendance_bp.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("attendance.login"))


@attendance_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return render_template("dashboard.html")

# API to create a new attendance record
@attendance_bp.route("/attendance", methods=["POST"])
def add_attendance():
    if is_holiday():
        return jsonify({"error": "Today is a holiday!"}), 400
    
    data = request.get_json()

    # Validate input data
    if not all(key in data for key in ["name", "date", "isPresent"]):
        return jsonify({"error": "Missing required fields: name, date, isPresent"}), 400

    try:
        # Convert date string to datetime.date object
        date_object = datetime.strptime(data["date"], "%Y-%m-%d").date()

        # Create a new attendance record
        new_record = Attendance(
            name=data["name"],
            date=date_object,
            isPresent=data["isPresent"]
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify({"message": "Attendance record added successfully!"}), 201
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API to get attendance for all employees for a specific month and year
@attendance_bp.route("/attendance/<int:year>/<int:month>", methods=["GET"])
def get_attendance_by_month(year, month):
    try:
        # Fetch records for the specific month and year
        records = Attendance.query.filter(
            db.extract("year", Attendance.date) == year,
            db.extract("month", Attendance.date) == month
        ).all()

        # Return the results
        return jsonify([
            {"id": record.id, "name": record.name, "date": str(record.date), "isPresent": record.isPresent}
            for record in records
        ]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to add a new holiday
@attendance_bp.route("/holidays", methods=["POST"])
def add_holiday():
    data = request.get_json()

    # Validate input data
    if "date" not in data:
        return jsonify({"error": "Missing required field: date"}), 400

    try:
        # Convert date string to datetime.date object
        date_object = datetime.strptime(data["date"], "%Y-%m-%d").date()

        # Create a new holiday record
        new_record = Holidays(date=date_object)
        db.session.add(new_record)
        db.session.commit()
        return jsonify({"message": "Holiday added successfully!"}), 201
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# @attendance_bp.route("/create_user", methods=["POST"])
# def create_user():
#     username = "admin"
#     password = "admin"
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

#     new_user = Users(username=username, password=hashed_password)
#     db.session.add(new_user)
#     db.session.commit()

#     return jsonify({"message": "User created successfully!"}), 201

# @attendance_bp.route("/check_user", methods=["GET"])
# def check_user():
#     username = "admin"
#     password = "admin"
#     user = Users.query.filter_by(username=username).first()
#     if user and bcrypt.checkpw(password.encode("utf-8"), user.password):
#         return jsonify({"message": "User exists!"}), 200
#     else:
#         return jsonify({"error": "User does not exist!"}), 404