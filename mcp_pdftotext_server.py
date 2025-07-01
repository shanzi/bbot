import subprocess
from mcp.server.fastmcp.server import FastMCP

fast_mcp = FastMCP("mcp-pdftotext-server")

@fast_mcp.tool()
def pdf_to_text(file_path: str) -> str:
    """
    Converts a PDF file to plain text using the 'pdftotext' command-line tool.
    Returns the extracted text content as a string.
    """
    try:
        # Ensure the file exists
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
