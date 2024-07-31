import os
import requests
from datetime import datetime
import csv
import gspread
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
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Get the Google Sheet ID from environment variables
spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')

# Open the Google Sheet using the Spreadsheet ID
spreadsheet = client.open_by_key(spreadsheet_id)

# Create a new sheet with the current date
worksheet = spreadsheet.add_worksheet(title=current_date, rows="1000", cols="20")

# Read the CSV file and update the Google Sheet
with open(filename, 'r') as file:
    reader = csv.reader(file)
    for row_index, row in enumerate(reader):
        worksheet.insert_row(row, row_index + 1)
