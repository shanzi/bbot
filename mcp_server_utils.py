"""MCP server providing utility tools for PDF processing, file management, email, and system monitoring."""

import json
import os
import subprocess
import tempfile
import time
import platform
import shutil

import tiktoken
from mcp.server.fastmcp.server import FastMCP

import utils

# Initialize MCP server and tiktoken encoding
fast_mcp = FastMCP("mcp-server-utils")
encoding = tiktoken.get_encoding("cl100k_base")

@fast_mcp.tool()
def download_file(url: str, subdirectory: str) -> str:
    """Download a file from the given URL with automatic filename detection.
    
    Args:
        url: The URL to download from
        subdirectory: Subdirectory under 'data' to save the file
        
    Returns:
        str: Success message with the saved file path or error message
    """
    try:
        saved_path = utils.download_file(url, subdirectory)
        filename = os.path.basename(saved_path)
        return f"File successfully downloaded as '{filename}' to {saved_path}"
    except Exception as e:
        return f"Failed to download file from {url}: {e}"

@fast_mcp.tool()
def pdf_to_text(file_path: str, truncate_limit_tokens: int = 500) -> str:
    """Convert a PDF file to plain text using the 'pdftotext' command-line tool.
    
    Args:
        file_path: Path to the PDF file
        truncate_limit_tokens: Maximum tokens to return (0 for full text)
        
    Returns:
        str: Extracted text or error message
    """
    try:
        # Ensure the file exists and is a PDF
        if not file_path.lower().endswith('.pdf'):
            return f"Error: The provided file is not a PDF: {file_path}"
        
        # Run pdftotext command
        result = subprocess.run(
            ["pdftotext", file_path, "-"],  # "-" tells pdftotext to output to stdout
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
        return (
            "Error: 'pdftotext' command not found. "
            "Please ensure it is installed and in your system's PATH."
        )
    except subprocess.CalledProcessError as e:
        return f"Error converting PDF with pdftotext: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


@fast_mcp.tool()
def pdf_to_images(
    file_path: str, 
    pages: list[int] = None, 
    image_format: str = "jpeg", 
    size: int = 1024
) -> str:
    """Convert selected pages of a PDF file into images using 'pdftocairo'.
    
    Args:
        file_path: Path to the PDF file
        pages: List of page numbers to convert (defaults to [1])
        image_format: Output format (png, jpeg, tiff, ps, eps, svg)
        size: Width of output images in pixels
        
    Returns:
        str: Success message with paths or error message
    """
    if pages is None:
        pages = [1]
        
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
            
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
        return f"PDF successfully converted to images: {','.join(output_paths)}"
    except FileNotFoundError:
        return (
            "Error: 'pdftocairo' command not found. "
            "Please ensure it is installed and in your system's PATH."
        )
    except subprocess.CalledProcessError as e:
        return f"Error converting PDF to images with pdftocairo: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@fast_mcp.tool()
def trim_pdf_margins(file_path: str, uniform_order_stat: int = 1) -> str:
    """Trim the margins of a PDF file using the 'pdfcropmargins' command-line tool.
    
    Args:
        file_path: Path to the PDF file
        uniform_order_stat: Order statistic for margin detection (higher = more aggressive)
        
    Returns:
        str: Success message or error message
    """
    try:
        if not file_path.lower().endswith('.pdf'):
            return f"Error: The provided file is not a PDF: {file_path}"

        output_dir = utils.get_save_directory("document", "cropped")
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.basename(file_path)
        output_file_path = os.path.join(output_dir, base_name)

        command = [
            "pdfcropmargins", "-v", "-s", "-m", 
            str(uniform_order_stat), file_path, "-o", output_file_path
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return f"PDF margins successfully trimmed. Output: {result.stdout}"
    except FileNotFoundError:
        return (
            "Error: 'pdfcropmargins' command not found. "
            "Please ensure it is installed and in your system's PATH."
        )
    except subprocess.CalledProcessError as e:
        return f"Error trimming PDF margins with pdfcropmargins: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@fast_mcp.tool()
def webpage_to_pdf(url: str, output_path: str, timeout: int = 60) -> str:
    """Convert a webpage to PDF using wkhtmltopdf with timeout handling.
    
    Args:
        url: The URL of the webpage to convert
        output_path: Path where the PDF should be saved
        timeout: Maximum time in seconds to wait for conversion (default: 60)
        
    Returns:
        str: Success or error message
    """
    try:
        utils.webpage_to_pdf(url, output_path, timeout)
        return f"Successfully converted {url} to {output_path} (timeout: {timeout}s)"
    except Exception as e:
        return f"Failed to convert {url} to PDF: {e}"

@fast_mcp.tool()
def get_pdf_info(file_path: str) -> str:
    """Get information about a PDF file using the 'pdfinfo' command-line tool.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: PDF information or error message
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
        return (
            "Error: 'pdfinfo' command not found. "
            "Please ensure it is installed and in your system's PATH."
        )
    except subprocess.CalledProcessError as e:
        return f"Error getting PDF info with pdfinfo: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@fast_mcp.tool()
def send_email(
    to_address: str, 
    subject: str, 
    body: str, 
    attachment_path: str = None
) -> str:
    """Send an email with an optional attachment from a Gmail account.
    
    Args:
        to_address: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_path: Optional path to file to attach
        
    Returns:
        str: Success or error message
    """
    try:
        utils.send_email(to_address, subject, body, attachment_path)
        return f"Email successfully sent to {to_address}"
    except Exception as e:
        return f"Failed to send email to {to_address}: {e}"

@fast_mcp.tool()
def send_to_kindle(attachment_path: str) -> str:
    """Send an email with an attachment to the Kindle email address.
    
    Args:
        attachment_path: Path to the file to send to Kindle
        
    Returns:
        str: Success or error message
    """
    try:
        utils.send_email_to_kindle(attachment_path)
        return f"Successfully sent {attachment_path} to Kindle."
    except Exception as e:
        return f"Failed to send {attachment_path} to Kindle: {e}"

@fast_mcp.tool()
def save_summary(summary: str, file_path: str) -> str:
    """Save the given summary to a file.
    
    Args:
        summary: The summary text to save
        file_path: Path where the summary should be saved
        
    Returns:
        str: Success or error message
    """
    try:
        utils.save_summary(summary, file_path)
        return f"Summary successfully saved to {file_path}"
    except Exception as e:
        return f"Failed to save summary to {file_path}: {e}"

@fast_mcp.tool()
def empty_trash() -> str:
    """Permanently delete all files and directories from the trash folder.
    
    Returns:
        str: Success or error message
    """
    try:
        utils.empty_trash()
        return "Trash has been emptied."
    except Exception as e:
        return f"Error emptying trash: {e}"

@fast_mcp.tool()
def get_system_overview() -> str:
    """Get a comprehensive system overview including CPU, memory, disk, and uptime.
    
    Returns:
        str: Complete system status overview
    """
    try:
        overview = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system": {
                "platform": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            }
        }
        
        # Get uptime
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["uptime"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                overview["uptime"] = result.stdout.strip()
            elif platform.system() == "Linux":
                with open("/proc/uptime", "r") as f:
                    uptime_seconds = float(f.read().split()[0])
                    days, remainder = divmod(uptime_seconds, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, _ = divmod(remainder, 60)
                    overview["uptime"] = f"up {int(days)} days, {int(hours)}:{int(minutes):02d}"
        except:
            overview["uptime"] = "Uptime unavailable"
        
        # Get load average
        try:
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                overview["load_average"] = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
        except:
            overview["load_average"] = "Load average unavailable"
        
        # Get basic memory info
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["top", "-l", "1", "-n", "0"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout
                for line in output.split('\n'):
                    if 'PhysMem:' in line:
                        overview["memory"] = line.strip()
                        break
            elif platform.system() == "Linux":
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.readlines()
                    for line in meminfo[:3]:
                        if "MemTotal" in line:
                            overview["memory_total"] = line.strip()
                        elif "MemFree" in line:
                            overview["memory_free"] = line.strip()
                        elif "MemAvailable" in line:
                            overview["memory_available"] = line.strip()
        except:
            overview["memory"] = "Memory info unavailable"
        
        # Get disk usage for root
        try:
            usage = shutil.disk_usage("/")
            overview["disk_usage"] = {
                "total": f"{usage.total / (1024**3):.1f} GB",
                "used": f"{usage.used / (1024**3):.1f} GB",
                "free": f"{usage.free / (1024**3):.1f} GB",
                "usage_percent": f"{(usage.used / usage.total * 100):.1f}%"
            }
        except:
            overview["disk_usage"] = "Disk usage unavailable"
        
        return json.dumps(overview, indent=2)
    except Exception as e:
        return f"Error getting system overview: {e}"

@fast_mcp.tool()
def get_cpu_info() -> str:
    """Get CPU information and current usage statistics.
    
    Returns:
        str: CPU information and usage statistics
    """
    try:
        cpu_info = {
            "processor": platform.processor(),
            "machine": platform.machine(),
            "architecture": platform.architecture(),
            "system": platform.system(),
            "release": platform.release()
        }
        
        # Get CPU usage using top command
        if platform.system() in ["Darwin", "Linux"]:
            try:
                if platform.system() == "Darwin":
                    result = subprocess.run(
                        ["top", "-l", "1", "-n", "0"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    output = result.stdout
                    for line in output.split('\n'):
                        if 'CPU usage:' in line:
                            cpu_info["usage"] = line.strip()
                            break
                else:
                    result = subprocess.run(
                        ["top", "-bn1"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    output = result.stdout
                    for line in output.split('\n'):
                        if '%Cpu' in line:
                            cpu_info["usage"] = line.strip()
                            break
            except:
                cpu_info["usage"] = "CPU usage data unavailable"
        
        # Get load average
        try:
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                cpu_info["load_average"] = {
                    "1_min": load_avg[0],
                    "5_min": load_avg[1],
                    "15_min": load_avg[2]
                }
        except:
            cpu_info["load_average"] = "Load average unavailable"
        
        return json.dumps(cpu_info, indent=2)
    except Exception as e:
        return f"Error getting CPU info: {e}"

@fast_mcp.tool()
def get_memory_info() -> str:
    """Get memory usage information.
    
    Returns:
        str: Memory usage statistics
    """
    try:
        memory_info = {}
        
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["vm_stat"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                memory_info["vm_stat"] = result.stdout.strip()
            except:
                memory_info["vm_stat"] = "VM statistics unavailable"
                
            try:
                result = subprocess.run(
                    ["top", "-l", "1", "-n", "0"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout
                for line in output.split('\n'):
                    if 'PhysMem:' in line:
                        memory_info["physical_memory"] = line.strip()
                        break
            except:
                memory_info["physical_memory"] = "Physical memory unavailable"
                
        elif platform.system() == "Linux":
            try:
                with open("/proc/meminfo", "r") as f:
                    memory_info["proc_meminfo"] = f.read().strip()
            except:
                memory_info["proc_meminfo"] = "Memory info unavailable"
        
        return json.dumps(memory_info, indent=2)
    except Exception as e:
        return f"Error getting memory info: {e}"

@fast_mcp.tool()
def get_disk_info() -> str:
    """Get disk usage information.
    
    Returns:
        str: Disk usage statistics
    """
    try:
        disk_info = {}
        
        try:
            result = subprocess.run(
                ["df", "-h"],
                capture_output=True,
                text=True,
                timeout=10
            )
            disk_info["disk_usage"] = result.stdout.strip()
        except:
            disk_info["disk_usage"] = "Disk usage unavailable"
        
        try:
            current_dir = os.getcwd()
            usage = shutil.disk_usage(current_dir)
            disk_info["current_directory"] = {
                "path": current_dir,
                "total": f"{usage.total / (1024**3):.2f} GB",
                "used": f"{usage.used / (1024**3):.2f} GB",
                "free": f"{usage.free / (1024**3):.2f} GB",
                "usage_percent": f"{(usage.used / usage.total * 100):.1f}%"
            }
        except:
            disk_info["current_directory"] = "Current directory usage unavailable"
            
        return json.dumps(disk_info, indent=2)
    except Exception as e:
        return f"Error getting disk info: {e}"

@fast_mcp.tool()
def get_process_info(limit: int = 10) -> str:
    """Get information about running processes.
    
    Args:
        limit: Maximum number of processes to return (default: 10)
    
    Returns:
        str: Process information
    """
    try:
        process_info = {}
        
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            elif platform.system() == "Linux":
                result = subprocess.run(
                    ["ps", "aux", "--sort=-pcpu"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            lines = result.stdout.strip().split('\n')
            process_info["header"] = lines[0]
            process_info["processes"] = lines[1:limit+1]
            
        except:
            process_info["processes"] = "Process info unavailable"
            
        return json.dumps(process_info, indent=2)
    except Exception as e:
        return f"Error getting process info: {e}"


def main() -> None:
    """Run the MCP server."""
    fast_mcp.run()


if __name__ == "__main__":
    main()
