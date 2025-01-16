import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()

SPREADSHEET_ID = '1Rc4COG0KWkeBh3MiIOIMONoCtCt1O9GjAHsNjjTAtNs'
RANGE_NAME = 'Jan 25!A1:Q23'
API_KEY = os.getenv('API_KEY')

def authenticate(API_KEY):
    return build('sheets', 'v4', developerKey=API_KEY).spreadsheets()

if __name__ == '__main__':
    service = authenticate(API_KEY=API_KEY)
    result = service.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
    else:
        for row in values:
            print(row)