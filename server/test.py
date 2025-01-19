import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import datetime

def authenticate(API_KEY):
    return build('sheets', 'v4', developerKey=API_KEY).spreadsheets()

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

if __name__ == '__main__':
    
    load_dotenv()

    date_time = datetime.datetime.now()
    day = date_time.day

    SPREADSHEET_ID = '1Rc4COG0KWkeBh3MiIOIMONoCtCt1O9GjAHsNjjTAtNs'
    RANGE_NAME = get_range_name(day)
    API_KEY = os.getenv('API_KEY')

    print(RANGE_NAME)

    service = authenticate(API_KEY=API_KEY)
    result = service.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
    else:
        for row in values:
            print(row)