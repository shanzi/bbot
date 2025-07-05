import asyncio
import httpx
import os


def get_save_directory(*args) -> str:
    return os.path.join(os.getcwd(), "data", *args)


def download_file(url: str, save_path: str):
    """
    Downloads a file from the given URL and saves it to the specified path.
    """
    # Sanitize file_name to prevent directory traversal
    save_directory = os.path.dirname(save_path)
    os.makedirs(save_directory, exist_ok=True)

    try:
        response = httpx.get(url, follow_redirects=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        with open(save_path, "wb") as f:
            f.write(response.content)
    except httpx.RequestError as e:
        raise ValueError(f"Error making HTTP request: {e}")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP error during download: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during download: {e}")


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from dotenv import load_dotenv

load_dotenv()

def send_email(to_address: str, subject: str, body: str, attachment_path: str = None):
    """
    Sends an email with an optional attachment from a Gmail account.
    Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD to be set as environment variables.
    """
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_app_password:
        raise ValueError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables must be set.")

    msg = MIMEMultipart()
    msg['From'] = gmail_address
    msg['To'] = to_address
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        if not os.path.exists(attachment_path):
            raise FileNotFoundError(f"Attachment file not found at: {attachment_path}")

        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f"attachment; filename= {os.path.basename(attachment_path)}",
        )
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_address, gmail_app_password)
        text = msg.as_string()
        server.sendmail(gmail_address, to_address, text)
        server.quit()
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during email sending: {e}")

import os
import subprocess
import tempfile

def webpage_to_pdf(url: str, output_path: str):
    """
    Converts a webpage to PDF using wkhtmltopdf.
    """
    tmp_output = tempfile.mktemp('temp.pdf')
    try:
        subprocess.run(
            ["wkhtmltopdf", url, tmp_output],
            check=True
        )
    except subprocess.CalledProcessError as e:
        if not os.path.exists(tmp_output):
            raise Exception(f"Error converting to PDF with wkhtmltopdf: {e.stderr}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")
    finally:
        if os.path.exists(tmp_output):
            os.rename(tmp_output, output_path)

def send_email_to_kindle(attachment_path: str):
    """
    Sends an email with an attachment to the Kindle email address.
    Requires GMAIL_ADDRESS, GMAIL_APP_PASSWORD, and KINDLE_ADDRESS to be set as environment variables.
    """
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    kindle_address = os.getenv("KINDLE_ADDRESS")

    if not gmail_address or not gmail_app_password or not kindle_address:
        raise ValueError("GMAIL_ADDRESS, GMAIL_APP_PASSWORD, and KINDLE_ADDRESS environment variables must be set.")

    msg = MIMEMultipart()
    msg['From'] = gmail_address
    msg['To'] = kindle_address

    if not os.path.exists(attachment_path):
        raise FileNotFoundError(f"Attachment file not found at: {attachment_path}")

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f"attachment; filename= {os.path.basename(attachment_path)}",
    )
    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_address, gmail_app_password)
        text = msg.as_string()
        server.sendmail(gmail_address, kindle_address, text)
        server.quit()
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during email sending: {e}")

def save_summary(summary: str, file_path: str):
    """
    Saves the given summary to a file.
    """
    try:
        with open(file_path, "w") as f:
            f.write(summary)
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during summary saving: {e}")


import shutil
import tiktoken

# Get the encoding for a default model.
# cl100k_base is the encoding used by gpt-4, gpt-3.5-turbo, and text-embedding-ada-002.
encoding = tiktoken.get_encoding("cl100k_base")

def get_trash_directory() -> str:
    """Returns the absolute path to the trash directory."""
    return os.path.join(os.getcwd(), "data", "trash")

def empty_trash():
    """
    Permanently deletes all files and subdirectories in the trash directory.
    """
    trash_dir = get_trash_directory()
    if not os.path.exists(trash_dir):
        return

    for filename in os.listdir(trash_dir):
        file_path = os.path.join(trash_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            raise ValueError(f"Failed to delete {file_path}. Reason: {e}")


def estimate_tokens(message_history: list) -> int:
    """
    Estimates the token count of a message history using the tiktoken library.
    """
    token_count = 0
    for message in message_history:
        # message is a PromptMessage object with a 'content' attribute
        # content can be a string or a list of content blocks
        content = message.content
        if isinstance(content, str):
            token_count += len(encoding.encode(content))
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, str):
                    token_count += len(encoding.encode(block))
                elif hasattr(block, 'text'):
                    token_count += len(encoding.encode(block.text))
    return token_count
