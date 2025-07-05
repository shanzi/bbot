import os
import utils
import tempfile
import subprocess
from mcp.server.fastmcp.server import FastMCP
import tiktoken

fast_mcp = FastMCP("mcp-server-utils")

@fast_mcp.tool()
def download_file(url: str, subdirectory: str, file_name: str) -> str:
    """
    Downloads a file from the given URL and saves it to the 'data' folder.
    The file must be saved in one subdirectory under 'data'.
    The assistant should decide which subdirectory to put per filetype.
    """
    # Sanitize file_name to prevent directory traversal
    try:
        save_dir = utils.get_save_directory(subdirectory)
        save_path = os.path.join(save_dir, file_name)
        utils.download_file(url, save_path)
        return f"File {file_name} successfully downloaded"
    except Exception as e:
        return f"Failed to download file {url}: {e}"

import tiktoken

# Get the encoding for a default model.
# cl100k_base is the encoding used by gpt-4, gpt-3.5-turbo, and text-embedding-ada-002.
encoding = tiktoken.get_encoding("cl100k_base")

@fast_mcp.tool()
def pdf_to_text(file_path: str, truncate_limit_tokens: int = 500) -> str:
    """
    Converts a PDF file to plain text using the 'pdftotext' command-line tool.
    By default, the returned text is truncated to 500 tokens.
    The agent can specify a different `truncate_limit_tokens` to get more or less text.
    Set `truncate_limit_tokens` to 0 to get the full text.
    """
    try:
        # Ensure the file exists and is a PDF
        if not file_path.lower().endswith('.pdf'):
            return f"Error: The provided file is not a PDF: {file_path}"
        
        # Run pdftotext command
        result = subprocess.run(
            ["pdftotext", file_path, "-"], # "-" tells pdftotext to output to stdout
            capture_output=True,
            text=True,
            check=True
        )
        
        full_text = result.stdout
        
        if truncate_limit_tokens > 0:
            tokens = encoding.encode(full_text)
            if len(tokens) > truncate_limit_tokens:
                truncated_tokens = tokens[:truncate_limit_tokens]
                return encoding.decode(truncated_tokens) + "\n\n... (truncated)"

        return full_text
        
    except FileNotFoundError:
        return "Error: 'pdftotext' command not found. Please ensure it is installed and in your system's PATH."
    except subprocess.CalledProcessError as e:
        return f"Error converting PDF with pdftotext: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


@fast_mcp.tool()
def pdf_to_images(file_path: str, pages: list[int] = [1], image_format: str = "jpeg", size: int = 1024) -> str:
    """
    Converts selected pages of a PDF file into images using the 'pdftocairo' command-line tool.
    By default, it only converts the first page to a 1024px wide jpeg image.
    The agent can specify a different page or list of pages, image format (png, jpeg, tiff, ps, eps, svg), and size.
    The output directory will be 'data/document/thumbnail'.
    Returns a comma-separated list of the full paths of the generated images.
    """
    try:
        if not file_path.lower().endswith('.pdf'):
            return f"Error: The provided file is not a PDF: {file_path}"

        output_directory = utils.get_save_directory("document", "thumbnail")
        os.makedirs(output_directory, exist_ok=True)

        # Determine the correct file extension
        extension = "jpg" if image_format == "jpeg" else image_format

        output_paths = []
        for page in pages:
            base_name = os.path.basename(file_path).replace('.pdf', '')
            output_prefix = os.path.join(output_directory, f"{base_name}_{page}")
            
            # The actual output path will have the correct extension
            output_path = f"{output_prefix}.{extension}"
            output_paths.append(output_path)

            command = [
                "pdftocairo", 
                f"-{image_format}", 
                "-f", 
                str(page), 
                "-scale-to",
                str(size),
                '-singlefile',
                file_path, 
                output_prefix
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
        return f"PDF successfully converted to images: {','.join(output_paths)}"
    except FileNotFoundError:
        return "Error: 'pdftocairo' command not found. Please ensure it is installed and in your system's PATH."
    except subprocess.CalledProcessError as e:
        return f"Error converting PDF to images with pdftocairo: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@fast_mcp.tool()
def trim_pdf_margins(file_path: str, uniform_order_stat: int = 1) -> str:
    """
    Trims the margins of a PDF file using the 'pdfcropmargins' command-line tool.
    By default, it uses a uniform order statistic of 1.
    The agent can specify a different `uniform_order_stat` to ignore more or less of the largest margins.
    The output file will be created in the 'data/document/cropped' directory.
    """
    try:
        if not file_path.lower().endswith('.pdf'):
            return f"Error: The provided file is not a PDF: {file_path}"

        output_dir = utils.get_save_directory("document", "cropped")
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.basename(file_path)
        output_file_path = os.path.join(output_dir, base_name)

        command = ["pdfcropmargins", "-v", "-s", "-m", str(uniform_order_stat), file_path, "-o", output_file_path]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return f"PDF margins successfully trimmed. Output: {result.stdout}"
    except FileNotFoundError:
        return "Error: 'pdfcropmargins' command not found. Please ensure it is installed and in your system's PATH."
    except subprocess.CalledProcessError as e:
        return f"Error trimming PDF margins with pdfcropmargins: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@fast_mcp.tool()
def webpage_to_pdf(url: str, output_path: str) -> str:
    """
    Converts a webpage to PDF using wkhtmltopdf.
    """
    try:
        utils.webpage_to_pdf(url, output_path)
        return f"Successfully converted {url} to {output_path}"
    except Exception as e:
        return f"Failed to convert {url} to PDF: {e}"

@fast_mcp.tool()
def get_pdf_info(file_path: str) -> str:
    """
    Returns information about a PDF file using the 'pdfinfo' command-line tool.
    """
    try:
        if not file_path.lower().endswith('.pdf'):
            return f"Error: The provided file is not a PDF: {file_path}"

        result = subprocess.run(
            ["pdfinfo", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except FileNotFoundError:
        return "Error: 'pdfinfo' command not found. Please ensure it is installed and in your system's PATH."
    except subprocess.CalledProcessError as e:
        return f"Error getting PDF info with pdfinfo: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@fast_mcp.tool()
def send_email(to_address: str, subject: str, body: str, attachment_path: str = None) -> str:
    """
    Sends an email with an optional attachment from a Gmail account.
    Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD to be set as environment variables.
    """
    try:
        utils.send_email(to_address, subject, body, attachment_path)
        return f"Email successfully sent to {to_address}"
    except Exception as e:
        return f"Failed to send email to {to_address}: {e}"

@fast_mcp.tool()
def send_to_kindle(attachment_path: str) -> str:
    """
    Sends an email with an attachment to the Kindle email address.
    Requires GMAIL_ADDRESS, GMAIL_APP_PASSWORD, and KINDLE_ADDRESS to be set as environment variables.
    """
    try:
        utils.send_email_to_kindle(attachment_path)
        return f"Successfully sent {attachment_path} to Kindle."
    except Exception as e:
        return f"Failed to send {attachment_path} to Kindle: {e}"

@fast_mcp.tool()
def save_summary(summary: str, file_path: str) -> str:
    """
    Saves the given summary to a file.
    The file will be saved in the same directory as the original document.
    """
    try:
        utils.save_summary(summary, file_path)
        return f"Summary successfully saved to {file_path}"
    except Exception as e:
        return f"Failed to save summary to {file_path}: {e}"

def main():
    fast_mcp.run()

if __name__ == "__main__":
    main()
