import os
import utils
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
        return f"File {sanitized_file_name} successfully downloaded"
    except Exception as e:
        return f"Failed to download file {url}: {e}"


def main():
    fast_mcp.run()

if __name__ == "__main__":
    main()
