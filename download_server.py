import asyncio
import httpx
import os
from mcp.server.fastmcp.server import FastMCP

fast = FastMCP("download-server")

@fast.tool()
def download_file(url: str, file_name: str) -> str:
    """
    Downloads a file from the given URL and saves it to the 'data' folder.
    The file will be saved in the 'data/document' subdirectory.
    """
    # Sanitize file_name to prevent directory traversal
    sanitized_file_name = os.path.basename(file_name)
    save_directory = os.path.join(os.getcwd(), "data", "document")
    os.makedirs(save_directory, exist_ok=True)
    save_path = os.path.join(save_directory, sanitized_file_name)

    try:
        response = httpx.get(url, follow_redirects=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        with open(save_path, "wb") as f:
            f.write(response.content)

        return f"File downloaded successfully to {save_path}"
    except httpx.RequestError as e:
        raise ValueError(f"Error making HTTP request: {e}")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP error during download: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during download: {e}")

def main(): # Changed to def main()
    fast.run()

if __name__ == "__main__":
    main()
