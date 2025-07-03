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
        utils.download_file(url, subdirectory, file_name)
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
def pdf_to_images(file_path: str, output_directory: str = None) -> str:
    """
    Converts a PDF file into images (PNG format by default) using the 'pdftocairo' command-line tool.
    Returns a message indicating the success or failure and the output directory.
    """
    try:
        if not file_path.lower().endswith('.pdf'):
            return f"Error: The provided file is not a PDF: {file_path}"

        if output_directory is None:
            output_directory = os.path.join(os.path.dirname(file_path), "pdf_images")
        
        os.makedirs(output_directory, exist_ok=True)

        # pdftocairo -png input.pdf output_prefix
        command = ["pdftocairo", "-png", file_path, os.path.join(output_directory, os.path.basename(file_path).replace('.pdf', ''))]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return f"PDF successfully converted to images in: {output_directory}. Output: {result.stdout}"
    except FileNotFoundError:
        return "Error: 'pdftocairo' command not found. Please ensure it is installed and in your system's PATH."
    except subprocess.CalledProcessError as e:
        return f"Error converting PDF to images with pdftocairo: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

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
