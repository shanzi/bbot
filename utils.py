import asyncio
import httpx
import os


def get_save_directory(*args) -> str:
    return os.path.join(os.getcwd(), "data", *args)


def download_file(url: str, subdir: str, file_name: str):
    """
    Downloads a file from the given URL and saves it to the 'data' folder.
    The file will be saved in the 'data/document' subdirectory.
    """
    # Sanitize file_name to prevent directory traversal
    save_directory = get_save_directory(subdir)
    os.makedirs(save_directory, exist_ok=True)
    sanitized_file_name = os.path.basename(file_name)

    save_path = os.path.join(save_directory, sanitized_file_name)

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
