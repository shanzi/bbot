"""Utility functions for file operations, email, and document processing."""

import os
import shutil
import smtplib
import subprocess
import tempfile
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
import tiktoken
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize tiktoken encoding for token estimation
# cl100k_base is the encoding used by gpt-4, gpt-3.5-turbo, and text-embedding-ada-002
ENCODING = tiktoken.get_encoding("cl100k_base")


def get_allowed_email_addresses() -> set:
    """Get the set of allowed email addresses for sending emails.
    
    Includes addresses from ALLOWED_EMAIL_ADDRESSES environment variable
    and automatically includes the Kindle address if configured.
    
    Returns:
        set: Set of allowed email addresses
    """
    allowed_addresses = set()
    
    # Get allowed addresses from environment variable (comma-separated)
    allowed_env = os.getenv("ALLOWED_EMAIL_ADDRESSES", "")
    if allowed_env:
        allowed_addresses.update(addr.strip() for addr in allowed_env.split(","))
    
    # Always include Kindle address if configured
    kindle_address = os.getenv("KINDLE_ADDRESS")
    if kindle_address:
        allowed_addresses.add(kindle_address.strip())
    
    return allowed_addresses


def get_save_directory(*args) -> str:
    """Get the absolute path to a subdirectory within the data folder.
    
    Args:
        *args: Path components to join with the data directory
        
    Returns:
        str: Absolute path to the requested directory
    """
    return os.path.join(os.getcwd(), "data", *args)


def download_file(url: str, subdirectory: str) -> str:
    """Download a file from the given URL with automatic filename detection.
    
    Args:
        url: The URL to download from
        subdirectory: Subdirectory under 'data' to save the file
        
    Returns:
        str: The full path where the file was saved
        
    Raises:
        ValueError: If there's an error during download
    """
    import mimetypes
    from urllib.parse import urlparse, unquote
    
    try:
        response = httpx.get(url, follow_redirects=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Try to detect filename from various sources
        filename = None
        
        # 1. Try Content-Disposition header
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('\\"')
            filename = unquote(filename)  # Decode URL encoding
        
        # 2. Try to extract from URL path
        if not filename:
            parsed_url = urlparse(url)
            url_filename = os.path.basename(parsed_url.path)
            if url_filename and '.' in url_filename:
                filename = unquote(url_filename)
        
        # 3. Generate filename based on content type
        if not filename:
            content_type = response.headers.get('content-type', '').split(';')[0]
            extension = mimetypes.guess_extension(content_type) or '.bin'
            
            # Create a more descriptive name based on domain and timestamp
            domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
            timestamp = int(time.time())
            filename = f"document_{domain}_{timestamp}{extension}"
        
        # Sanitize filename to prevent directory traversal and handle special characters
        filename = os.path.basename(filename)  # Remove any path components
        filename = "".join(c if c.isalnum() or c in '.-_ ()[]{}' else '_' for c in filename)
        
        # Ensure we have a file extension
        if '.' not in filename:
            content_type = response.headers.get('content-type', '').split(';')[0]
            extension = mimetypes.guess_extension(content_type) or '.bin'
            filename += extension
        
        # Create save path
        save_directory = get_save_directory(subdirectory)
        os.makedirs(save_directory, exist_ok=True)
        save_path = os.path.join(save_directory, filename)
        
        # Handle filename conflicts by adding a number
        counter = 1
        original_save_path = save_path
        while os.path.exists(save_path):
            name, ext = os.path.splitext(original_save_path)
            save_path = f"{name}_{counter}{ext}"
            counter += 1

        with open(save_path, "wb") as f:
            f.write(response.content)
            
        return save_path
        
    except httpx.RequestError as e:
        raise ValueError(f"Error making HTTP request: {e}") from e
    except httpx.HTTPStatusError as e:
        raise ValueError(
            f"HTTP error during download: {e.response.status_code} - {e.response.text}"
        ) from e
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during download: {e}") from e


def send_email(to_address: str, subject: str, body: str, attachment_path: str = None) -> None:
    """Send an email with an optional attachment from a Gmail account.
    
    Args:
        to_address: Recipient email address
        subject: Email subject line
        body: Email body text
        attachment_path: Optional path to file to attach
        
    Raises:
        ValueError: If environment variables are missing, recipient not allowed, or email sending fails
        FileNotFoundError: If attachment file doesn't exist
    """
    # Check if the recipient is in the allow list
    allowed_addresses = get_allowed_email_addresses()
    if not allowed_addresses:
        raise ValueError(
            "No allowed email addresses configured. Set ALLOWED_EMAIL_ADDRESSES environment variable."
        )
    
    if to_address not in allowed_addresses:
        raise ValueError(
            f"Email address '{to_address}' is not in the allowed list. "
            f"Please add it to ALLOWED_EMAIL_ADDRESSES environment variable."
        )
    
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_app_password:
        raise ValueError(
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables must be set."
        )

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
        raise ValueError(f"An unexpected error occurred during email sending: {e}") from e

def webpage_to_pdf(url: str, output_path: str) -> None:
    """Convert a webpage to PDF using wkhtmltopdf.
    
    Args:
        url: The URL of the webpage to convert
        output_path: The path where the PDF should be saved
        
    Raises:
        Exception: If conversion fails
    """
    tmp_output = tempfile.mktemp('temp.pdf')
    try:
        subprocess.run(
            ["wkhtmltopdf", url, tmp_output],
            check=True
        )
    except subprocess.CalledProcessError as e:
        if not os.path.exists(tmp_output):
            raise Exception(f"Error converting to PDF with wkhtmltopdf: {e.stderr}") from e
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e
    finally:
        if os.path.exists(tmp_output):
            os.rename(tmp_output, output_path)

def send_email_to_kindle(attachment_path: str) -> None:
    """Send an email with an attachment to the Kindle email address.
    
    Args:
        attachment_path: Path to the file to send to Kindle
        
    Raises:
        ValueError: If environment variables are missing or email sending fails
        FileNotFoundError: If attachment file doesn't exist
    """
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    kindle_address = os.getenv("KINDLE_ADDRESS")

    if not gmail_address or not gmail_app_password or not kindle_address:
        raise ValueError(
            "GMAIL_ADDRESS, GMAIL_APP_PASSWORD, and KINDLE_ADDRESS environment variables must be set."
        )

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
        raise ValueError(f"An unexpected error occurred during email sending: {e}") from e

def save_summary(summary: str, file_path: str) -> None:
    """Save the given summary to a file.
    
    Args:
        summary: The summary text to save
        file_path: The path where the summary should be saved
        
    Raises:
        ValueError: If file writing fails
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(summary)
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during summary saving: {e}") from e


def get_trash_directory() -> str:
    """Get the absolute path to the trash directory.
    
    Returns:
        str: Absolute path to the trash directory
    """
    return os.path.join(os.getcwd(), "data", "trash")


def empty_trash() -> None:
    """Permanently delete all files and subdirectories in the trash directory.
    
    Raises:
        ValueError: If deletion of any file/directory fails
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
            raise ValueError(f"Failed to delete {file_path}. Reason: {e}") from e


def estimate_tokens(message_history: list) -> int:
    """Estimate the token count of a message history using the tiktoken library.
    
    Args:
        message_history: List of PromptMessage objects with content attributes
        
    Returns:
        int: Estimated token count for the message history
    """
    token_count = 0
    for message in message_history:
        # message is a PromptMessage object with a 'content' attribute
        # content can be a string or a list of content blocks
        content = message.content
        if isinstance(content, str):
            token_count += len(ENCODING.encode(content))
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, str):
                    token_count += len(ENCODING.encode(block))
                elif hasattr(block, 'text'):
                    token_count += len(ENCODING.encode(block.text))
    return token_count
