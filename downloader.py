import os
import json
import requests
from datetime import datetime
import csv
import gspread
from collections import defaultdict
from oauth2client.service_account import ServiceAccountCredentials

# Get current date
current_date = datetime.now().strftime("%Y-%m-%d")

# URL of the block deals report
url = 'https://nsearchives.nseindia.com/content/equities/block.csv'

# Headers to mimic a real browser visit
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Send a GET request to the URL
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Save the content to a file with the current date in the filename
    filename = f'block_deals_{current_date}.csv'
    with open(filename, 'wb') as file:
        file.write(response.content)
    print(f"Download successful! Saved as {filename}")
else:
    print(f"Failed to download the report. Status code: {response.status_code}")

# Google Sheets integration
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_dict = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)

# Get the Google Sheet ID from environment variables
spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')

# Open the Google Sheet using the Spreadsheet ID
spreadsheet = client.open_by_key(spreadsheet_id)

# Read the CSV file and organize data by symbol
symbol_data = defaultdict(list)
header = None

with open(filename, 'r') as file:
    reader = csv.reader(file)
    for row_index, row in enumerate(reader):
        if row_index == 0:
            header = row[1:]  # Save the header without the first column
        else:
            symbol = row[1]
            symbol_data[symbol].append(row[1:])  # Remove the first column

# Append new data to the master sheet
master_sheet_name = "MasterSheet"
try:
    master_sheet = spreadsheet.worksheet(master_sheet_name)
except gspread.exceptions.WorksheetNotFound:
    master_sheet = spreadsheet.add_worksheet(title=master_sheet_name, rows="1000", cols="20")

# Prepare new data with date header and space
master_header = [f"Date: {current_date}"]
empty_row = [''] * len(header)

# Insert header and space at the top of the master sheet
master_sheet.insert_row(empty_row, index=1)
master_sheet.insert_row(master_header, index=1)
master_sheet.insert_row(empty_row, index=2)
master_sheet.insert_row(header, index=3)

# Insert new data below the header and space in master sheet
for row_index, row in enumerate(sum(symbol_data.values(), [])):
    master_sheet.insert_row(row, row_index + 4)  # Adjust index to account for header and space

# Insert two rows of space after the new data in master sheet
master_sheet.insert_row(empty_row, index=len(sum(symbol_data.values(), [])) + 5)
master_sheet.insert_row(empty_row, index=len(sum(symbol_data.values(), [])) + 6)

# Function to append data to a symbol sheet with date header and space
def append_to_symbol_sheet(symbol, data):
    try:
        sheet = spreadsheet.worksheet(symbol)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=symbol, rows="1000", cols="20")

    # Prepare new data with date header and space
    date_header = [f"Date: {current_date}"]
    empty_row = [''] * len(data[0])

    # Insert header and space at the top of the symbol sheet
    sheet.insert_row(empty_row, index=1)
    sheet.insert_row(date_header, index=1)
    sheet.insert_row(empty_row, index=2)
    sheet.insert_row(header, index=3)

    # Insert new data below the header and space
    for row_index, row in enumerate(data):
        sheet.insert_row(row, row_index + 4)  # Adjust index to account for header and space

    # Insert two rows of space after the new data
    sheet.insert_row(empty_row, index=len(data) + 5)
    sheet.insert_row(empty_row, index=len(data) + 6)

# Append data to the respective symbol sheets
for symbol, data in symbol_data.items():
    append_to_symbol_sheet(symbol, data)
