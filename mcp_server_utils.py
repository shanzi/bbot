import os
import utils
import tempfile
import subprocess
from mcp.server.fastmcp.server import FastMCP

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
        utils.download_file(url, subdirectory, file_name)
        return f"File {file_name} successfully downloaded"
    except Exception as e:
        return f"Failed to download file {url}: {e}"

@fast_mcp.tool()
def pdf_to_text(file_path: str) -> str:
    """
    Converts a PDF file to plain text using the 'pdftotext' command-line tool.
    Returns the extracted text content as a string.
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
        return result.stdout
    except FileNotFoundError:
        return "Error: 'pdftotext' command not found. Please ensure it is installed and in your system's PATH."
    except subprocess.CalledProcessError as e:
        return f"Error converting PDF with pdftotext: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def main():
    fast_mcp.run()

if __name__ == "__main__":
    main()
