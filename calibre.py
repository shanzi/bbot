"""Calibre ebook management module for adding, listing, and converting ebooks."""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class CalibreManager:
    """Calibre ebook management controller."""
    
    def __init__(self, library_path: Optional[str] = None):
        """Initialize Calibre manager.
        
        Args:
            library_path: Path to Calibre library (optional, uses CALIBRE_LIBRARY_PATH env var)
        """
        self.library_path = library_path or os.getenv("CALIBRE_LIBRARY_PATH", 
                                                      os.path.expanduser("~/Calibre Library"))
        
        logger.info(f"Initializing CalibreManager with library path: {self.library_path}")
        
        # Ensure library directory exists
        os.makedirs(self.library_path, exist_ok=True)
        
        # Log directory contents for debugging
        if os.path.exists(self.library_path):
            try:
                contents = os.listdir(self.library_path)
                logger.info(f"Library directory contents: {contents}")
                logger.info(f"Library directory exists: {os.path.exists(self.library_path)}")
                logger.info(f"Library directory is readable: {os.access(self.library_path, os.R_OK)}")
            except Exception as e:
                logger.error(f"Error listing library directory: {e}")
    
    def add_ebook(self, file_path: str, title: Optional[str] = None, 
                  authors: Optional[str] = None) -> Dict[str, Any]:
        """Add an ebook to the Calibre library.
        
        Args:
            file_path: Path to the ebook file
            title: Optional title override
            authors: Optional authors override
            
        Returns:
            dict: Result information with success status and details
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "book_id": None
            }
        
        try:
            cmd = [
                "calibredb", "add", file_path,
                "--library-path", self.library_path
            ]
            
            # Add metadata if provided
            if title:
                cmd.extend(["--title", title])
            if authors:
                cmd.extend(["--authors", authors])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract book ID from output
            book_id = None
            for line in result.stdout.split('\n'):
                if "Added book ids:" in line:
                    # Extract ID from "Added book ids: 123"
                    try:
                        book_id = int(line.split(":")[1].strip())
                    except (IndexError, ValueError):
                        pass
            
            return {
                "success": True,
                "message": f"Successfully added ebook: {os.path.basename(file_path)}",
                "book_id": book_id,
                "file_path": file_path
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to add ebook: {e.stderr}",
                "book_id": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "book_id": None
            }
    
    def list_ebooks(self, search_query: Optional[str] = None, 
                    limit: int = 20) -> Dict[str, Any]:
        """List ebooks in the Calibre library.
        
        Args:
            search_query: Optional search query (e.g., "author:King", "title:Python")
            limit: Maximum number of results to return
            
        Returns:
            dict: List of ebooks with metadata
        """
        logger.info(f"Listing ebooks: search_query='{search_query}', limit={limit}")
        logger.info(f"Using library path: {self.library_path}")
        
        try:
            cmd = [
                "calibredb", "list",
                "--library-path", self.library_path,
                "--fields", "id,title,authors,formats,size,timestamp",
                f"--limit", str(limit)
            ]
            
            if search_query:
                cmd.extend(["-s", search_query])
            
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Command exit code: {result.returncode}")
            logger.info(f"Command stdout length: {len(result.stdout)} chars")
            logger.info(f"Command stdout: {repr(result.stdout[:500])}...")  # First 500 chars
            if result.stderr:
                logger.warning(f"Command stderr: {result.stderr}")
            
            books = []
            raw_output = result.stdout.strip()
            
            logger.info(f"Raw output length: {len(raw_output)} chars")
            
            # Use a simpler approach: try with --separator to get machine-readable output
            logger.info("Trying alternative parsing approach...")
            
            # Re-run the command with different format for better parsing
            cmd_alt = [
                "calibredb", "list",
                "--library-path", self.library_path,
                "--fields", "id,title,authors",
                f"--limit", str(limit),
                "--separator", "|||"  # Use unique separator
            ]
            
            if search_query:
                cmd_alt.extend(["-s", search_query])
            
            logger.info(f"Executing alternative command: {' '.join(cmd_alt)}")
            
            result_alt = subprocess.run(
                cmd_alt,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Alternative command stdout: {repr(result_alt.stdout[:500])}...")
            
            lines = result_alt.stdout.strip().split('\n')
            
            # Skip header line if present
            if lines and 'id|||title|||authors' in lines[0]:
                lines = lines[1:]
                logger.info(f"Skipped header line, processing {len(lines)} data lines")
            
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                
                logger.debug(f"Processing line {i}: {repr(line)}")
                parts = line.split('|||')
                logger.debug(f"Line parts count: {len(parts)}, parts: {parts}")
                
                if len(parts) >= 3:
                    try:
                        book_id = int(parts[0].strip())
                        title = parts[1].strip() if parts[1].strip() else "Unknown Title"
                        authors = parts[2].strip() if parts[2].strip() else "Unknown Author"
                        
                        book = {
                            "id": book_id,
                            "title": title,
                            "authors": authors,
                            "formats": "",  # We'll get this separately if needed
                            "size": "0",
                            "timestamp": ""
                        }
                        books.append(book)
                        logger.info(f"Added book: {book}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse line {i}: {e}, parts: {parts}")
                        continue
                else:
                    logger.warning(f"Line {i} has insufficient parts ({len(parts)}): {parts}")
            
            logger.info(f"Final books count: {len(books)}")
            
            return {
                "success": True,
                "books": books,
                "count": len(books),
                "library_path": self.library_path
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"calibredb command failed: {e}")
            logger.error(f"Command: {' '.join(cmd)}")
            logger.error(f"Exit code: {e.returncode}")
            logger.error(f"Stderr: {e.stderr}")
            logger.error(f"Stdout: {e.stdout}")
            return {
                "success": False,
                "error": f"Failed to list ebooks: {e.stderr}",
                "books": []
            }
        except Exception as e:
            logger.error(f"Unexpected error in list_ebooks: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "books": []
            }
    
    def convert_ebook(self, input_path: str, output_format: str = "pdf",
                      output_path: Optional[str] = None, **options) -> Dict[str, Any]:
        """Convert an ebook to different format.
        
        Args:
            input_path: Path to input ebook file
            output_format: Target format (pdf, epub, mobi, etc.)
            output_path: Optional output path (auto-generated if not provided)
            **options: Additional conversion options
            
        Returns:
            dict: Conversion result with output path
        """
        if not os.path.exists(input_path):
            return {
                "success": False,
                "error": f"Input file not found: {input_path}",
                "output_path": None
            }
        
        # Generate output path if not provided
        if not output_path:
            input_file = Path(input_path)
            output_path = str(input_file.with_suffix(f'.{output_format.lower()}'))
        
        try:
            cmd = ["ebook-convert", input_path, output_path]
            
            # Add common conversion options
            if output_format.lower() == "pdf":
                cmd.extend(["--pdf-page-numbers"])
                if options.get("page_breaks", True):
                    cmd.extend(["--page-breaks-before", "/"])
            
            if output_format.lower() == "mobi":
                cmd.extend(["--output-profile", "kindle"])
            
            # Add custom options
            for key, value in options.items():
                if key not in ["page_breaks"]:  # Skip processed options
                    cmd.extend([f"--{key.replace('_', '-')}", str(value)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "success": True,
                "message": f"Successfully converted to {output_format.upper()}",
                "input_path": input_path,
                "output_path": output_path,
                "format": output_format.upper()
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Conversion failed: {e.stderr}",
                "output_path": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "output_path": None
            }
    
    def get_book_info(self, book_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific book.
        
        Args:
            book_id: Calibre book ID
            
        Returns:
            dict: Book information and metadata
        """
        try:
            cmd = [
                "calibredb", "show_metadata", str(book_id),
                "--library-path", self.library_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse metadata output
            metadata = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            return {
                "success": True,
                "book_id": book_id,
                "metadata": metadata
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to get book info: {e.stderr}",
                "metadata": {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": {}
            }
    
    def export_book(self, book_id: int, output_dir: str, 
                   formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """Export book files from library.
        
        Args:
            book_id: Calibre book ID
            output_dir: Directory to export files to
            formats: Specific formats to export (None for all)
            
        Returns:
            dict: Export result with file paths
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                "calibredb", "export", str(book_id),
                "--library-path", self.library_path,
                "--to-dir", output_dir,
                "--single-dir"
            ]
            
            if formats:
                cmd.extend(["--formats", ",".join(formats)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find exported files
            exported_files = []
            for file_path in Path(output_dir).rglob('*'):
                if file_path.is_file():
                    exported_files.append(str(file_path))
            
            return {
                "success": True,
                "message": f"Exported book ID {book_id}",
                "book_id": book_id,
                "output_dir": output_dir,
                "exported_files": exported_files
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Export failed: {e.stderr}",
                "exported_files": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "exported_files": []
            }


# Global Calibre instance for easy access
calibre_manager = CalibreManager()


def main():
    """Example usage of Calibre manager."""
    print("Calibre Library Manager")
    print(f"Library path: {calibre_manager.library_path}")
    
    # List existing books
    result = calibre_manager.list_ebooks(limit=10)
    if result["success"]:
        print(f"\nFound {result['count']} books:")
        for book in result["books"][:5]:  # Show first 5
            print(f"  {book['id']:3d}. {book['title']} by {book['authors']}")
    
    print("\nExample conversion:")
    print("calibre_manager.convert_ebook('input.epub', 'pdf')")
    print("\nExample adding book:")
    print("calibre_manager.add_ebook('/path/to/book.epub', title='My Book', authors='Author Name')")


if __name__ == "__main__":
    main()