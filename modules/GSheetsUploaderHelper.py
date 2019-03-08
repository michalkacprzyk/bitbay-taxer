#!/usr/bin/env python3
# mk (c) 2018

# https://developers.google.com/sheets/api/quickstart/python
# Requires: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
# Likely within an venv
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class GSheetsUploaderHelper:
    """
    A handy helper for Google Sheets APIv4 actions.
    https://developers.google.com/sheets/api/
    """

    # A service account JSON file, its email is added to shared in the sheets we access
    CLIENT_SECRET_FILE = ''

    # Obtained from the sheet URL
    SPREADSHEET_ID = ''

    # API Scope: https://developers.google.com/api-client-library/python/auth/service-accounts
    SCOPE = ['https://www.googleapis.com/auth/spreadsheets']

    SERVICE = ''

    def __init__(self, client_secret_file, spreadsheet_id):
        self.CLIENT_SECRET_FILE = client_secret_file
        self.SPREADSHEET_ID = spreadsheet_id
        self.SERVICE = self.get_service()

    def get_service(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CLIENT_SECRET_FILE, self.SCOPE)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)

        return service

    def read_data(self, range_name):
        """
        Simple read mk_data function
        :param range_name: e.g. A1:D4
        :return: List of lists, one per row of mk_data
        """
        result = self.SERVICE.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID, range=range_name).execute()
        return result.get('values', [])

    def write_data(self, values, range_name, mode):
        """
        Simple write mk_data function
        :param values: List of lists containing mk_data, one list per row e.g. [[1, 2, 3], [4, 5, 6]]
        :param range_name: e.g. A1:B3
        :param mode: 'USER_ENTERED' or 'RAW' - how should the mk_data be processed
        :return: Result object. E.g. result.get('updatedCells')
        """

        body = {'values': values}

        result = self.SERVICE.spreadsheets().values().update(
            spreadsheetId=self.SPREADSHEET_ID, range=range_name,
            valueInputOption=mode, body=body).execute()
        return result

    def update_document_title(self, new_title):
        """
        https://developers.google.com/sheets/api/guides/batchupdate#example
        :return:
        """
        body = {
              "requests": [{
                  "updateSpreadsheetProperties": {
                    "properties": {"title": new_title},
                    "fields": "title"
                  }
              }]
        }

        result = self.SERVICE.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID, body=body).execute()
        return result

    def update_sheet_title(self, sheet_nr, new_title):
        body = {
             "requests": [{
                "updateSheetProperties": {
                    "properties": {
                       "sheetId": sheet_nr,
                       "title": new_title,
                },
                    "fields": "title",
                }
             }]
        }

        result = self.SERVICE.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID, body=body).execute()
        return result

    def get_sheet_properties(self):
        """
        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/get
        :return:
        """
        request = self.SERVICE.spreadsheets().get(spreadsheetId=self.SPREADSHEET_ID, ranges=[], includeGridData=False)
        return request.execute()

    def format_borders(self):
        """
        https://developers.google.com/sheets/api/samples/formatting
        :return:
        """

        properties = self.get_sheet_properties()
        sheet_id = properties['sheets'][0]['properties']['sheetId']

        body = {
           "requests": [
             {
               "updateBorders": {
                 "range": {
                   "sheetId": sheet_id,
                   "startRowIndex": 0,
                   "endRowIndex": 10,
                   "startColumnIndex": 0,
                   "endColumnIndex": 6
                 },
                 "top": {
                   "style": "DASHED",
                   "width": 1,
                   "color": {
                   "blue": 1.0
                 },
                 },
                 "bottom": {
                   "style": "DASHED",
                   "width": 1,
                   "color": {
                   "blue": 1.0
                 },
                 },
                 "innerHorizontal": {
                   "style": "DASHED",
                   "width": 1,
                   "color": {
                       "blue": 1.0
                   },
                 },
               }
             }
          ]
        }

        result = self.SERVICE.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID, body=body).execute()
        return result

    def format_header(self):

        properties = self.get_sheet_properties()
        sheet_id = properties['sheets'][0]['properties']['sheetId']

        body = {
          "requests": [
            {
              "repeatCell": {
                "range": {
                  "sheetId": sheet_id,
                  "startRowIndex": 0,
                  "endRowIndex": 1
                },
                "cell": {
                  "userEnteredFormat": {
                    "backgroundColor": {
                      "red": 12.0,
                      "green": 12.0,
                      "blue": 12.0
                    },
                    "horizontalAlignment" : "CENTER",
                    "textFormat": {
                     "fontSize": 12,
                     "bold": True
                    }
                  }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
              }
            },
            {
              "updateSheetProperties": {
                "properties": {
                  "sheetId": sheet_id,
                  "gridProperties": {
                    "frozenRowCount": 1
                  }
                },
                "fields": "gridProperties.frozenRowCount"
              }
            }
          ]
        }

        result = self.SERVICE.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID, body=body).execute()
        return result

    def format_values(self, rows_nr):

        properties = self.get_sheet_properties()
        sheet_id = properties['sheets'][0]['properties']['sheetId']

        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {  # Date
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": rows_nr,
                            "startColumnIndex": 1,
                            "endColumnIndex": 2
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "DATE",
                                    "pattern": "dd-mm-yyyy hh:mm:ss"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                },
                {
                    "repeatCell": {
                        "range": {  # Rate
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": rows_nr,
                            "startColumnIndex": 4,
                            "endColumnIndex": 5
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "NUMBER",
                                    "pattern": "#,##0.00 zł"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                },
                {
                    "repeatCell": {
                        "range": {  # Amount
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": rows_nr,
                            "startColumnIndex": 5,
                            "endColumnIndex": 6
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "NUMBER",
                                    "pattern": "0.000000000"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": rows_nr,
                            "startColumnIndex": 7,
                            "endColumnIndex": 12
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "NUMBER",
                                    "pattern": "#,##0.00 zł"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                },
            ]
        }

        result = self.SERVICE.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID, body=body).execute()
        return result


def test():
    """
    Simple test function, not all features are implemented
    :return:
    """

    msh = GSheetsUploaderHelper('client_secret.json', '1TDXDUDXgu6GS5v9NQTRwFzt6To3rwKr9vyYsaXCuDms')

    print("[i] Get sheet properties")
    print(msh.get_sheet_properties())

    values_w = [['1', '2', '3'], ['4', '5', '6']]
    my_range = "A1:C3"

    print("[i] Write some mk_data")
    print(values_w)
    msh.write_data(values_w, my_range, 'RAW')

    print("[i] Reading mk_data")
    values_r = msh.read_data(my_range)
    print(values_r)

    assert(values_w == values_r)

    print("[i] Updating title")
    msh.update_title("API Test")
    print("[i] Formatting borders")
    msh.format_borders()
    print("[i] Formatting header")
    msh.format_header()
    print("[i] Formatting values")
    msh.format_values()

# test()
