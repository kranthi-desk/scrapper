import PyPDF2
import requests
from bs4 import BeautifulSoup
import os
import csv
import time
from concurrent.futures import ThreadPoolExecutor
import re
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import random

# Configuration: Replace these with your actual details
pdf_path = './list.pdf'          # Path to the PDF with support page links
resume_path = './resume.pdf' # Path to your resume file
gmail_user = 'GMAIL'
gmail_password = 'PASSWORD'    # Your Gmail App Password
csv_file = './emails.csv'           # Output CSV file to store URLs and emails
CREDENTIALS_FILE = 'creds.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

def extract_links_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        links = []
        for page in reader.pages:
            if '/Annots' in page:
                for annot in page['/Annots']:
                    obj = annot.get_object()
                    if '/A' in obj and '/URI' in obj['/A']:
                        links.append(obj['/A']['/URI'])
    return links

# Step 2: Fetch email from a single webpage with debugging
def fetch_email_from_url(url):
    try:
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()

        # Parse final page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try finding mailto links first
        mailto_links = soup.find_all('a', href=lambda x: x and x.startswith('mailto:'))
        if mailto_links:
            raw_email = mailto_links[0]['href'].replace('mailto:', '')
            email_match = re.match(r'[^?]+', raw_email)
            email = email_match.group(0) if email_match else raw_email
            # Validate email contains '@'
            if '@' in email:
                print(f'Found email {email} for {url} via mailto')
                return (url, email)
            else:
                print(f'Invalid mailto content "{email}" for {url}, falling back to regex')

        # Fallback to regex search in page text
        page_text = soup.get_text()
        email_matches = EMAIL_REGEX.findall(page_text)
        if email_matches:
            email = email_matches[0]  # Take the first email found
            print(f'Found email {email} for {url} via regex')
            return (url, email)
        else:
            print(f'No email found for {url}')
            return (url, None)
    except requests.exceptions.RequestException as e:
        print(f'Failed to access {url}: {e}')
        return (url, None)

# Step 3: Save emails to CSV
def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['URL', 'Email'])
        writer.writerows(data)

# Step 4: Authenticate with Gmail API
def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, 
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # OOB for manual code
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f'Please visit this URL to authorize this application: {auth_url}')
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

# Step 5: Send email with resume using Gmail API
def send_email(to_email, resume_path, service):
    try:
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = 'Seeking Software Engineering Opportunities (Remote or On-Site)'
        
        # Customized email body with your details
        body = """Dear Hiring Consultant,

I hope this message finds you well. My name is XXXX, and I am reaching out to explore software engineering opportunities through your esteemed consultancy, either remotely or on-site. I am based out of India and bring a strong background in technology, with a B.Tech in Computer Science and Engineering from IIT Bombay (GPA: 7.6/10) and 1.5 years of professional experience at BrowserStack, complemented by an internship at Indeed. I am eager to collaborate with your team to connect with clients who can benefit from my expertise in Ruby on Rails, Node.js, Python, and cloud technologies.

During my tenure at XXXX as a Software Engineer since XXXX. My technical skill set includes Python, Java, C++, Node.js, Ruby on Rails, and tools like MySQL, Redis, PostgreSQL, AWS, BigQuery, and Git. I’ve applied these skills in innovative projects, such as a Restaurant Management System (ReactJS, Node.js) and Notify Me (Python, Django).

I’ve attached my resume for your review and would be delighted to discuss how my background can add value to your clients’ projects. I’m available at +919999999999 or via LinkedIn at https://www.linkedin.com/in/XXXX to explore potential opportunities or next steps.

Thank you for your time and consideration. I look forward to the possibility of working together to find a role where I can make a meaningful impact.

Best regards,  
XXXX  
+919999999999  
https://www.linkedin.com/in/XXXX"""
        
        msg.attach(MIMEText(body, 'plain'))

        with open(resume_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(resume_path)}')
            msg.attach(part)

        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        message = {'raw': raw_msg}
        service.users().messages().send(userId='me', body=message).execute()
        print(f'Sent email to {to_email}')
    except Exception as e:
        print(f'Failed to send email to {to_email}: {e}')

if __name__ == "__main__":
    print("Extracting links from PDF...")
    links = extract_links_from_pdf(pdf_path)

    print("Fetching emails with multithreading...")
    email_data = []
    email_count = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(fetch_email_from_url, links)
        email_data = list(results)
        email_count = sum(1 for _, email in email_data if email)

    print(f"Saving emails to {csv_file}...")
    save_to_csv(email_data, csv_file)

    print("Authenticating with Gmail API...")
    service = get_gmail_service()

    print("Sending emails sequentially...")
    for url, email in email_data:
        if email:
            send_email(email, resume_path, service)
            time.sleep(random.randint(0, 30))

    print(f"Process completed! Total emails found: {email_count}")