# Email Scraper and Sender

This script scrapes email addresses from URLs listed in a PDF file and sends emails with an attached resume using the Gmail API.

## Prerequisites

- Python 3.x
- Required Python packages (install using `pip install -r requirements.txt`):
  - PyPDF2
  - requests 
  - beautifulsoup4
  - google-auth-oauthlib
  - google-api-python-client

## Setup

1. **Clone the repository**:
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Prepare the required files**:
    - [resume.pdf](http://_vscodecontentref_/1): Your resume file to be attached to the emails
    - [creds.json](http://_vscodecontentref_/2): Credentials file for Gmail API (OAuth 2.0 client ID)

4. **Update the configuration in [send.py](http://_vscodecontentref_/3)**:
    - Replace `gmail_user` with your Gmail address
    - Replace `gmail_password` with your Gmail App Password
    - Replace `body` with the correct email body

## Usage

1. **Run the script**:
    ```sh
    python send.py
    ```

2. **Follow the instructions**:
    - The script will extract links from [list.pdf](http://_vscodecontentref_/4)
    - It will scrape email addresses from the extracted links
    - It will save the scraped email addresses to [emails.csv](http://_vscodecontentref_/5)
    - It will authenticate with the Gmail API
    - It will send emails with your resume attached to the scraped email addresses

## Files

- [send.py](http://_vscodecontentref_/6): The main script to run
- [list.pdf](http://_vscodecontentref_/7): PDF file containing URLs
- [resume.pdf](http://_vscodecontentref_/8): Your resume file  
- [creds.json](http://_vscodecontentref_/9): Credentials file for Gmail API
- [emails.csv](http://_vscodecontentref_/10): Output CSV file to store URLs and emails

## Notes

- The script uses multithreading to speed up the email scraping process
- The script includes error handling to manage failed requests and invalid email addresses
