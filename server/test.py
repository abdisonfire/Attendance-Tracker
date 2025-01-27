import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import datetime
from dateutil.rrule import rrule, DAILY
from calendar import monthrange
from datetime import date, timedelta

def authenticate(credentials):
    return build('sheets', 'v4', credentials=credentials).spreadsheets()

def get_column(day):
    column = day + ord('A')
    if column > ord('Z'):
        column = 'A' + chr(column - ord('Z') + ord('A') - 1)
    else:
        column = chr(column)
    return column

def get_sheet_name():
    return 'Jan 25'

def get_employee_count():
    return 22

def get_range_name(day):
    column = get_column(day)
    return get_sheet_name() + '!' + column + '2:' + column + str(get_employee_count() + 1)

def get_holidays(start_date, end_date):
    holidays = []
    for dt in rrule(DAILY, dtstart=start_date, until=end_date):
        dt = dt.date()
        if dt.weekday() == 4 or dt.weekday() == 5:
            holidays.append(dt)
    return holidays

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

if __name__ == '__main__':
    
    load_dotenv('.env')

    date_time = datetime.datetime.now()
    day = date_time.day

    SPREADSHEET_ID = '1Rc4COG0KWkeBh3MiIOIMONoCtCt1O9GjAHsNjjTAtNs'
    RANGE_NAME = get_range_name(day)
    API_KEY = os.getenv('API_KEY')

    print(RANGE_NAME)
    credentials = Credentials.from_service_account_file('key.json')
    service = authenticate(credentials=credentials)
    
    # body = {
    #     "requests": [
    #         {
    #             "addSheet": {
    #                 "properties": {
    #                     "title": "Feb 25",
    #                     "index": 3,
    #                     "gridProperties": {
    #                         "rowCount": 100,
    #                         "columnCount": 29
    #                     }
    #                 }
    #             }
    #         }
    #     ]
    # }
    employees = [("RASHED", "A"), ("ARSIL", "B"), ("ASIF PARTHO", "A"), ("SUJAN", "B"), ("ARIF", "A"), ("MOBARAK", "A"), ("ZOHA", "A"), ("ASIF MIMI RABBI", "A"), ("TUSHAR", "B"), ("TALAT", "A"), ("TAWSIF", "A"), ("TARIF", "A"), ("IKRAMUL MURAD", "A"), ("SAMIN", "B"), ("SHAYANUL HAQ SADI", "A"), ("MD AZIZUR RAHMAN", "A"), ("ASIF NEWAZ", "A"), ("Fahim", "A"), ("Hasib", "B"), ("Noor", "A"), ("Rafi", "A"), ("Abdullah", "A")]
    employees = [employee[0] for employee in employees]
    start_date = date(2025, 2, 1)
    end_date = date(2025, 2, monthrange(2025, 2)[1])
    sheet_id = create_sheet(sheet_title="Feb 25", sheet_index=3, row_count=30, column_count=(end_date-start_date).days + 2)
    body = initialize_sheet(sheet_id=sheet_id, start_date=start_date, end_date=end_date, employees=employees, holidays=get_holidays(start_date, end_date))

    response = service.batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()

    # body = {"requests": remove_holiday(sheet_id, date(2025, 2, 8), start_date, len(employees), [])}

    # response = service.batchUpdate(
    #     spreadsheetId=SPREADSHEET_ID,
    #     body=body
    # ).execute()

    # Extract the sheetId of the newly created sheet
    # sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
    # print(f"New sheetId: {sheet_id}")
    print(response)

    # result = service.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    # values = result.get('values', [])
    # if not values:
    #     print('No data found.')
    # else:
    #     for row in values:
    #         print(row)