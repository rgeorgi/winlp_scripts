"""
The budget spreadsheet gets used for a lot of things,
so consolidate some of the functionality here
"""

import os
import pickle
from typing import Tuple, List

import googleapiclient.discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from winlp_scripts.utils import col_letter

class AuthenticationException(Exception): pass
class SheetParseException(Exception): pass

def get_sheet_by_index(service, spreadsheet_id, index) -> dict:
    """
    Return spreadsheet properties from the index
    """
    sheets = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute().get('sheets')
    for sheet in sheets:
        if sheet.get('properties', {}).get('index') == index:
            return sheet['properties']

def get_col(row, key, mapping):
    """
    Given a key for a column name,
    look up what column that maps to
    in the budget_mapping.yml, and return
    the given value
    """
    if key not in mapping:
        raise KeyError('No key "{}" in budget mapping'.format(key))
    index = col_letter(mapping.get(key))
    if index >= len(row):
        return None
    return row[index]

def auth_google(cred_path: str,
                client_path: str) -> Credentials:
    """

    """
    creds = None
    if os.path.exists(cred_path):
        with open(cred_path, 'rb') as cred_f:
            creds = pickle.load(cred_f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_path,
                ['https://www.googleapis.com/auth/spreadsheets.readonly'])
            creds = flow.run_local_server(port=0)
            with open(cred_path, 'wb') as token:
                pickle.dump(creds, token)
    return creds



def grab_sheet(spreadsheet_id: str,
               page_index: int,
               cred_path: Credentials=None,
               num_rows=1000,
               api_key: str=None,
               last_col='zz') -> Tuple[List, List]:
    """
    Grab the budget spreadsheet to process.
    """
    if not spreadsheet_id:
        raise SheetParseException("Spreadsheet_id must not be None")
    if not (cred_path or api_key):
        raise AuthenticationException('Either api_key or creds must be specified')

    if cred_path:
        creds = auth_google(cred_path)
        service = googleapiclient.discovery.build('sheets', 'v4', credentials=creds)
    elif api_key:
        service = googleapiclient.discovery.build('sheets', 'v4', developerKey=api_key)

    sheet_title = get_sheet_by_index(service, spreadsheet_id, page_index).get('title')
    rows = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="'{}'!A1:{}{}".format(sheet_title, last_col, num_rows)
    ).execute().get('values')
    headers = rows[0]
    return headers, rows[1:num_rows]

