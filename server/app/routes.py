from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from . import db
from .models import Attendance, Holidays, Users, Employees, Leaves, Sheets
from datetime import datetime, date
from dateutil.rrule import rrule, DAILY
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import bcrypt
from calendar import monthrange, month_name
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os

SPREADSHEET_ID = '1Rc4COG0KWkeBh3MiIOIMONoCtCt1O9GjAHsNjjTAtNs'
API_KEY = os.getenv('API_KEY')

def authenticate(credentials):
    return build('sheets', 'v4', credentials=credentials).spreadsheets()

def authenticate(credentials):
    return build('sheets', 'v4', credentials=credentials).spreadsheets()

def create_sheet(sheet_title, sheet_index, row_count, column_count):
    body = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": sheet_title,
                        "index": sheet_index,
                        "gridProperties": {
                            "rowCount": row_count,
                            "columnCount": column_count
                        }
                    }
                }
            }
        ]
    }
    try:
        response = service.batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
        return sheet_id
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def initialize_sheet(sheet_id, start_date, end_date, employees, holidays):
    requestsList = []
    flag = False
    row_index = 1
    col_index = 0
    background_color = {
        "red": 0.663,
        "green": 0.663,
        "blue": 0.663
    }
    clear_color = {
        "red": 1,
        "green": 1,
        "blue": 1
    }

    requestsList.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": len(employees) + 1,
                "startColumnIndex": 0,
                "endColumnIndex": (end_date-start_date).days + 2
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "textFormat": {
                        "bold": True
                    }
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,textFormat)"
        }
    })

    for employee in employees:
        requestsList.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_index,
                    "endRowIndex": row_index + 1,
                    "startColumnIndex": col_index,
                    "endColumnIndex": col_index + 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": background_color if flag else clear_color,
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "textFormat": {
                            "bold": True
                        }
                    },
                    "userEnteredValue": {
                        "stringValue": employee
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment),userEnteredValue"
            }
        })
        flag = not flag
        row_index += 1

    # Update row height
    requestsList.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 1,
                "endIndex": len(employees) + 1
            },
            "properties": {
                "pixelSize": 50
            },
            "fields": "pixelSize"
        }
    })
    
    # Update column width
    requestsList.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": (end_date-start_date).days + 2
            },
            "properties": {
                "pixelSize": 200
            },
            "fields": "pixelSize"
        }
    })
    row_index = 0
    col_index = 1

    for dt in rrule(DAILY, dtstart=start_date, until=end_date):
        dt = dt.date().strftime("%m/%d/%Y")
        requestsList.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_index,
                    "endRowIndex": row_index + 1,
                    "startColumnIndex": col_index,
                    "endColumnIndex": col_index + 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 0.0,
                            "green": 0.35,
                            "blue": 0.0
                        },
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "textFormat": {
                            "foregroundColor": {
                                "red": 1,
                                "green": 1,
                                "blue": 1
                            },
                            "bold": True
                        }
                    },
                    "userEnteredValue": {
                        "stringValue": dt
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment),userEnteredValue"
            }
        })
        col_index += 1

    requestsList.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex":  1,
                "startColumnIndex": 0,
                "endColumnIndex":  1
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {
                        "red": 0.0,
                        "green": 0.35,
                        "blue": 0.0
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "textFormat": {
                        "foregroundColor": {
                            "red": 1,
                            "green": 1,
                            "blue": 1
                        },
                        "bold": True
                    }
                },
                "userEnteredValue": {
                    "stringValue": ""
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment),userEnteredValue"
        }
    })

    for holiday in holidays:
        requestsList = add_holiday(sheet_id, holiday, start_date, len(employees), requestsList)

    body = {"requests": requestsList}
    return body

def add_holiday(sheet_id, holiday, start_date, employees_count, requestsList):
    index = (holiday - start_date).days + 1
    requestsList.append({
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": employees_count + 1,
                "startColumnIndex": index,
                "endColumnIndex": index + 1
            },
            "mergeType": "MERGE_ALL"
        }
    })
    requestsList.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": index,
                "endIndex": index+1
            },
            "properties": {
                "pixelSize": 80
            },
            "fields": "pixelSize"
        }
    })
    requestsList.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": employees_count + 1,
                "startColumnIndex": index,
                "endColumnIndex":  index+1
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {
                        "red": 1.0,
                        "green": 0.0,
                        "blue": 0.0
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "textFormat": {
                        "foregroundColor": {
                            "red": 1,
                            "green": 1,
                            "blue": 1
                        },
                        "bold": True
                    }
                },
                "userEnteredValue": {
                    "stringValue": "Holiday"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment),userEnteredValue"
        }
    })
    return requestsList

def remove_holiday(sheet_id, holiday, start_date, employees_count, requestsList):
    index = (holiday - start_date).days + 1
    requestsList.append({
        "unmergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": employees_count + 1,
                "startColumnIndex": index,
                "endColumnIndex": index + 1
            }
        }
    })
    requestsList.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": index,
                "endIndex": index+1
            },
            "properties": {
                "pixelSize": 200
            },
            "fields": "pixelSize"
        }
    })
    requestsList.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": employees_count + 1,
                "startColumnIndex": index,
                "endColumnIndex":  index+1
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {
                        "red": 1.0,
                        "green": 1.0,
                        "blue": 1.0
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "textFormat": {
                        "foregroundColor": {
                            "red": 0,
                            "green": 0,
                            "blue": 0
                        },
                        "bold": True
                    }
                },
                "userEnteredValue": {
                    "stringValue": ""
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment),userEnteredValue"
        }
    })
    return requestsList

def get_column(day):
    column = day + ord('A')
    if column > ord('Z'):
        column = 'A' + chr(column - ord('Z') + ord('A') - 1)
    else:
        column = chr(column)
    return column

def get_range_name(sheet_name, employee_count, column):
    return sheet_name + '!' + column + '2:' + column + str(employee_count + 1)

def get_holidays(start_date, end_date):
    holidays = []
    for dt in rrule(DAILY, dtstart=start_date, until=end_date):
        dt = dt.date()
        if dt.weekday() == 4 or dt.weekday() == 5 or Holidays.query.filter_by(date=dt).first() is not None:
            holidays.append(dt)
    
    return holidays

credentials = Credentials.from_service_account_file('key.json')
service = authenticate(credentials=credentials)

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
def is_holiday(day = None):
    today = datetime.now().date()
    if day is not None:
        today = day
    first = Holidays.query.filter_by(date=today).first() is not None # Check if today is a special holiday
    second = today.weekday() == 4 or today.weekday() == 5 # Friday or Saturday
    return first or second

def get_fine(count):
    if count == 0:
        return 100
    fine = 0
    if count > 8:
        fine = (count - 8) * 500 + 1200
    elif count > 4:
        fine = (count - 4) * 300 + 400
    else:
        fine = count * 100

    return fine

def is_created(sheet_name):
    try:
        result = service.values().get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A1:A2").execute()
        values = result.get('values', [])
        return True
    except Exception as e:
        return False
    
def get_sheet_id(sheet_name):
    sheet = Sheets.query.filter_by(sheet_name=sheet_name).first()
    if sheet is not None:
        return sheet.sheet_id
    return None

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

@attendance_bp.route("/create_sheet/<int:year>/<int:month>", methods=["GET"])
def create_sheet_for_month(year, month):
    try:
        sheet_name = f"{month_name[month]} {year}"
        if is_created(sheet_name):
            return jsonify({"message": "Sheet already exists!"}), 200

        employees = Employees.query.all()
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        holidays = get_holidays(start, end)
        sheet_id = create_sheet(sheet_name, 3, len(employees) + 1, (end-start).days + 2)

        new_sheet = Sheets(sheet_id=sheet_id, sheet_name=sheet_name)
        db.session.add(new_sheet)
        db.session.commit()

        body = initialize_sheet(sheet_id, start, end, [employee.name for employee in employees], holidays)
        response = service.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
        return redirect(url_for("attendance.get_attendance_by_month", year=year, month=month))
    except Exception as e:
        print(e)
        return redirect(url_for("attendance.get_attendance_by_month", year=year, month=month))

@attendance_bp.route("/dashboard/<int:year>/<int:month>", methods=["GET"])
def get_attendance_by_month(year, month):
    try:
        final_result = {"dates": [], "employees": [], "year": year, "month": month, "isCreated": False, "holidays": [], "sheet_id": None}
        sheet_name = f"{month_name[month]} {year}"
        sheet_id = get_sheet_id(sheet_name)
        if not is_created(sheet_name) or sheet_id is None:
            return render_template("attendance.html", data=final_result)
        
        final_result["isCreated"] = True
        final_result["sheet_id"] = sheet_id

        # Fetch records for the specific month and year
        emplpyees = Employees.query.all()

        # Return the results
        today = datetime.now().date()
        for i in range(len(emplpyees)):
            temp = { "attendance": [], "employee_name": emplpyees[i].name, "fine": 0}
            start = date(year, month, 1)
            end = date(year, month, monthrange(year, month)[1])
            for dt in rrule(DAILY, dtstart=start, until=end):
                dt = dt.date()
                if i == 0:
                    final_result["dates"].append(dt.strftime("%m/%d/%Y"))
                if is_holiday(day=dt):
                    temp["attendance"].append("H")
                elif Leaves.query.filter_by(date=dt, employee_id=emplpyees[i].id).first() is not None:
                    temp["attendance"].append("L")
                else:
                    attendance = Attendance.query.filter_by(date=dt, employee_id=emplpyees[i].id).first()
                    temp["attendance"].append("Not yet" if today < dt else "A" if attendance is None else "A" if attendance.isPresent else "P")
            temp["fine"] = get_fine(temp["attendance"].count("A"))
            final_result["employees"].append(temp)
        final_result["holidays"] = get_holidays_by_month(year, month)
        print(final_result["holidays"])

        return render_template("attendance.html", data=final_result)
    except Exception as e:
        print(e)
        # print(final_result)
        return render_template("error.html")

# API to add a new holiday
@attendance_bp.route("/add_holiday/<int:year>/<int:month>", methods=["POST"])
def add_special_holiday(year, month):
    # data = request.get_json(force=True)

    if request.form.get("date") is None:
        return redirect(url_for("attendance.get_attendance_by_month", year=year, month=month))

    holiday = datetime.strptime(request.form['date'], "%Y-%m-%d").date()

    try:
        # Convert date string to datetime.date object
        date_object = holiday
        # Check if thee date is already a holiday
        if Holidays.query.filter_by(date=date_object).first() is not None:
            return redirect(url_for("attendance.get_attendance_by_month", year=year, month=month))
        # Create a new holiday record
        new_record = Holidays(date=date_object)
        db.session.add(new_record)
        db.session.commit()

        sheet_name = f"{month_name[month]} {year}"
        sheet_id = get_sheet_id(sheet_name)
        start_date = date(year, month, 1)
        employees = Employees.query.all()
        requestsList = add_holiday(sheet_id, holiday, start_date, len(employees), [])

        body = {"requests": requestsList}
        response = service.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

        return redirect(url_for("attendance.get_attendance_by_month", year=year, month=month))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# API to remove a holiday
@attendance_bp.route("/remove_holiday/<int:year>/<int:month>/<int:day>", methods=["GET"])
def remove_special_holiday(year, month, day):
    # data = request.get_json(force=True)


    holiday = date(year, month, day)

    try:
        # Convert date string to datetime.date object
        date_object = holiday
        # Check if thee date is already a holiday
        record = Holidays.query.filter_by(date=date_object).first()
        if record is None:
            return redirect(url_for("attendance.get_attendance_by_month", year=year, month=month))
        db.session.delete(record)
        db.session.commit()

        sheet_name = f"{month_name[month]} {year}"
        sheet_id = get_sheet_id(sheet_name)
        start_date = date(year, month, 1)
        employees = Employees.query.all()
        requestsList = remove_holiday(sheet_id, holiday, start_date, len(employees), [])

        body = {"requests": requestsList}
        response = service.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

        return redirect(url_for("attendance.get_attendance_by_month", year=year, month=month))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# API to get all holidays for a specific month and year
def get_holidays_by_month(year, month):
    try:
        result = []
        days = monthrange(year, month)[1]
        for day in range(1, days+1):
            holiday = Holidays.query.filter_by(date=date(year, month, day)).first()
            if holiday is not None:
                result.append(holiday.date)
        return result
    except Exception as e:
        print(e)
        return []
    
#API to update leaves from sheet
@attendance_bp.route("/update/<int:year>/<int:month>", methods=["GET"])
def update_leaves(year, month):
    sheet_name = f"{month_name[month]} {year}"
    sheet_id = get_sheet_id(sheet_name)
    if sheet_id is None:
        return redirect(url_for("attendance.get_attendance_by_month", year=year, month=month))
    
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    employees = Employees.query.all()
    range_name = get_range_name(sheet_name, len(employees), 'C')
    result = service.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    employee_names = result.get('values', [])
    employee_names = [name[0] for name in employee_names]
    print(employee_names)

    # for dt in rrule(DAILY, dtstart=start_date, until=end_date):
    #     dt = dt.date()
    #     column = get_column(dt.day)
    #     for i in range(len(employees)):
    #         range_name = sheet_name + '!' + column + str(i+2)
    #         result = service.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    #         values = result.get('values', [])
            # print(values)
            # if values[i][0] == "L":
            #     employee = Employees.query.filter_by(name=employee_names[i]).first()
            #     leave = Leaves.query.filter_by(date=dt, employee_id=employee.id).first()
            #     if leave is None:
            #         new_leave = Leaves(date=dt, employee_id=employee.id)
            #         db.session.add(new_leave)

    requestsList = []
 
    result = service.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    values = result.get('values', [])

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

# @attendance_bp.route("/add_employees", methods=["GET"])
# def add_employees():
#     employees = [("RASHED", "A"), ("ARSIL", "B"), ("ASIF PARTHO", "A"), ("SUJAN", "B"), ("ARIF", "A"), ("MOBARAK", "A"), ("ZOHA", "A"), ("ASIF MIMI RABBI", "A"), ("TUSHAR", "A"), ("TALAT", "A"), ("TAWSIF", "A"), ("TARIF", "A"), ("IKRAMUL MURAD", "A"), ("SAMIN", "B"), ("SHAYANUL HAQ SADI", "A"), ("MD AZIZUR RAHMAN", "A"), ("ASIF NEWAZ", "A"), ("Fahim", "A"), ("Hasib", "B"), ("Noor", "A"), ("Rafi", "A"), ("Abdullah", "A")]
#     for employee in employees:
#         new_employee = Employees(name=employee[0], time_slot=employee[1])
#         db.session.add(new_employee)
#     db.session.commit()
#     return jsonify({"message": "Employees added successfully!"}), 201