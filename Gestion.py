import os 
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseUpload
import streamlit as st
from io import BytesIO
from paddleocr import PaddleOCR

SCOPES=["https://www.googleapis.com/auth/drive"]
creds=None
if os.path.exists("token.json"):
    creds=Credentials.from_authorized_user_file("token.json",SCOPES)
    
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow=InstalledAppFlow.from_client_secrets_file("credentials.json",SCOPES)
        creds=flow.run_local_server(port=0)
        
    with open('token.json','w') as token:
        token.write(creds.to_json())
        


def check_and_create_directory(service, folder_name):
    # Search for the folder by name
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    try:
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get("files", [])
        
        # If folder exists, return its ID
        if folders:
            print(f"Directory '{folder_name}' already exists with ID: {folders[0]['id']}")
            return folders[0]['id']
        else:
            # Folder doesn't exist, so create it
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            print(f"Directory '{folder_name}' created with ID: {folder.get('id')}")
            return folder.get('id')
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
    
    
def upload_file_to_folder(service, folder_id, file_path, file_name):
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]  # Specify the folder ID as the parent
    }
    media = MediaFileUpload(file_path, resumable=True)
    
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"File '{file_name}' uploaded successfully with ID: {file.get('id')}")
    except HttpError as error:
        print(f"An error occurred: {error}")
        
        
       
def upload_streamlit_file_to_folder(service, folder_id, uploaded_file):
    file_metadata = {
        'name': uploaded_file.name,
        'parents': [folder_id]  # Specify the folder ID as the parent
    }
    
    # Use MediaIoBaseUpload to upload from BytesIO
    media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type, resumable=True)
    
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"File '{uploaded_file.name}' uploaded successfully with ID: {file.get('id')}")
    except HttpError as error:
        print(f"An error occurred: {error}") 
        
        
import numpy as np
from PIL import Image
from pdfminer.high_level import extract_text

from paddleocr import PaddleOCR
from pdfminer.high_level import extract_text
from PIL import Image
from io import BytesIO
import numpy as np

def extract_text_from_file(file):
    # Check the file type based on file header
    file_header = file.read(4)
    file.seek(0)  # Reset file pointer

    if file_header[:4] == b'%PDF':
        # If the file is a PDF, use PDFMiner to extract text
        pdf_text = extract_text(file)
        print(pdf_text)
        return pdf_text.strip()

    else:
        # Assume it's an image; proceed with OCR extraction
        ocr = PaddleOCR(use_angle_cls=False, lang='en')
        
        # Read image as bytes and convert to PIL Image
        image_bytes = file.read()
        image = Image.open(BytesIO(image_bytes)).convert('RGB')  # Convert to RGB format

        # Convert PIL Image to NumPy array
        image_np = np.array(image)

        # Perform OCR on the image
        results = ocr.ocr(image_np)
        
        # Extract and combine text from results
        extracted_text = " ".join([line[1][0] for line in results[0]])

        return extracted_text



import re
from typing import List

def find_dates(text: str) -> List[str]:
    # Regular expression pattern to match various date formats
    date_pattern = r"""
        # Match dates in MM/DD/YYYY or MM-DD-YYYY format
        (?:[1-9]|0[1-9]|1[012])[-/](?:0[1-9]|[1-2][0-9]|3[01]|[1-9])[-/](?:19[0-9][0-9]|2[01][0-9][0-9])| 
        # Match dates in YYYY/MM/DD or YYYY-MM-DD format
        (?:19[0-9][0-9]|2[01][0-9][0-9])[-/](?:[1-9]|0[1-9]|1[012])[-/](?:0[1-9]|[1-2][0-9]|3[01]|[1-9])|
        # Match dates in DD/MM/YYYY or DD-MM-YYYY format
        (?:0[1-9]|[1-2][0-9]|3[01]|[1-9])[-/](?:[1-9]|0[1-9]|1[012])[-/](?:19[0-9][0-9]|2[01][0-9][0-9])|
        # Match dates with month names
        (?:[Jj][aA][nN][vV][iI][eE][rR]|[Ff][éeE][vV][rR][iI][eE][rR]|[mM][aA][rR][sS]|[Aa][vV][rR][iI][lL]|[mM][aA][iI]|[jJ][uU][iI][nN]|[jJ][uU][iI][eE][lL][eE][tT]|[Aa][oO][uU][tT]|[sS][eE][pP][tT][eE][mM][bB][rR][eE]|[Oo][Cc][tT][oO][bB][rR][eE]|[Nn][oO][vV][eE][mM][bB][Rr][eE]|[dD][éEe][cC][eE][mM][bB][Rr][eE]),[\s]?[0123]?[0-9],?[\s]?(?:19[0-9][0-9]|2[01][0-9][0-9])
    """
    
    # Find all matches in the text
    matches = re.findall(date_pattern, text, re.VERBOSE)
    dates=[match for match in matches if len(match)!=0]
    # Return unique matches
    return list(set(dates))

    

st.set_page_config(page_title="Upload File to Google Drive", page_icon=":cloud:")
st.image("feat.png", width=150)
    
st.title("Upload Facture to Google Drive")
uploaded_file = st.file_uploader("Choose a file to upload to Google Drive")

def check_and_create_subfolder(service, parent_folder_id, subfolder_name):
    # Search for the subfolder by name within the specified parent folder
    query = f"name='{subfolder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents"
    try:
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get("files", [])
        
        # If subfolder exists, return its ID
        if folders:
            print(f"Subfolder '{subfolder_name}' already exists with ID: {folders[0]['id']}")
            return folders[0]['id']
        else:
            # Subfolder doesn't exist, so create it
            file_metadata = {
                'name': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]  # Set the parent to the existing folder
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            print(f"Subfolder '{subfolder_name}' created with ID: {folder.get('id')}")
            return folder.get('id')
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


# In your Streamlit app, update this part:
if uploaded_file:
    # Authenticate and check or create directory, then upload the Streamlit file
    service = build("drive", "v3", credentials=creds)
    folder_name = "Test_folder"
    folder_id = check_and_create_directory(service, folder_name)
    
    # Extract text and find dates
    extracted_text = extract_text_from_file(uploaded_file)
    dates = find_dates(extracted_text)
    st.subheader("Extracted Dates")
    st.write(dates)
    st.subheader("Extracted Text")
    st.write(extract_text)

    if folder_id and dates:
        # Use the first date to create a subfolder
        subfolder_name = dates[0]
        subfolder_id = check_and_create_subfolder(service, folder_id, subfolder_name)
        
        # Upload the file to the new subfolder
        if subfolder_id:
            upload_streamlit_file_to_folder(service, subfolder_id, uploaded_file)


