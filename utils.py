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


def save_summary(summary: str, file_path: str):
    """
    Saves the given summary to a file.
    """
    try:
        with open(file_path, "w") as f:
            f.write(summary)
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during summary saving: {e}")


import tiktoken

# Get the encoding for a default model.
# cl100k_base is the encoding used by gpt-4, gpt-3.5-turbo, and text-embedding-ada-002.
encoding = tiktoken.get_encoding("cl100k_base")

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
