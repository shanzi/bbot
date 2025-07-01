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
def document_to_markdown(file_path: str) -> str:
    """
    Converts a document (e.g., PDF, DOCX) to Markdown using Pandoc.
    Returns the Markdown content as a string.
    """
    try:
        # Ensure the file exists
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        # Run pandoc command
        result = subprocess.run(
            ["pandoc", "-s", file_path, "-t", "markdown"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error converting document with Pandoc: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def main():
    fast_mcp.run()

if __name__ == "__main__":
    main()
