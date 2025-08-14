"""
Common Utility Functions
Helper functions used across the tournament management system
"""

import os
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object to string"""
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse datetime string to datetime object"""
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError:
        return None


def get_current_timestamp() -> str:
    """Get current timestamp as formatted string"""
    return format_datetime(datetime.now())


def add_minutes_to_datetime(dt: datetime, minutes: int) -> datetime:
    """Add minutes to a datetime object"""
    return dt + timedelta(minutes=minutes)


def format_duration_minutes(minutes: int) -> str:
    """Convert minutes to human-readable duration"""
    if minutes < 60:
        return f"{minutes} minutes"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length with optional suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def normalize_string(text: str) -> str:
    """Normalize string by stripping whitespace and converting to lowercase"""
    return text.strip().lower() if text else ""


def create_directory_if_not_exists(dir_path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {dir_path}: {e}")
        return False


def read_csv_file(file_path: str) -> Tuple[bool, List[Dict], List[str]]:
    """
    Read CSV file and return data with error handling
    Returns (success, data_list, error_messages)
    """
    errors = []
    data = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate headers exist
            if not reader.fieldnames:
                return False, [], ["CSV file has no headers"]

            for row_num, row in enumerate(reader, start=2):
                # Clean row data
                clean_row = {}
                for key, value in row.items():
                    clean_row[key.strip().lower()] = value.strip() if value else ""

                data.append(clean_row)

        return True, data, []

    except FileNotFoundError:
        return False, [], [f"File not found: {file_path}"]
    except PermissionError:
        return False, [], [f"Permission denied: {file_path}"]
    except UnicodeDecodeError:
        return False, [], [f"File encoding error: {file_path} (must be UTF-8)"]
    except Exception as e:
        return False, [], [f"Error reading CSV file: {e}"]


def write_csv_file(file_path: str, data: List[Dict], headers: List[str]) -> Tuple[bool, List[str]]:
    """
    Write data to CSV file
    Returns (success, error_messages)
    """
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

        return True, []

    except PermissionError:
        return False, [f"Permission denied: {file_path}"]
    except Exception as e:
        return False, [f"Error writing CSV file: {e}"]


def load_json_file(file_path: str) -> Tuple[bool, Optional[Dict], List[str]]:
    """
    Load JSON file safely
    Returns (success, data, error_messages)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, data, []

    except FileNotFoundError:
        return False, None, [f"File not found: {file_path}"]
    except json.JSONDecodeError as e:
        return False, None, [f"Invalid JSON format: {e}"]
    except Exception as e:
        return False, None, [f"Error reading JSON file: {e}"]


def save_json_file(file_path: str, data: Dict) -> Tuple[bool, List[str]]:
    """
    Save data to JSON file
    Returns (success, error_messages)
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True, []

    except Exception as e:
        return False, [f"Error saving JSON file: {e}"]


def format_table_data(headers: List[str], rows: List[List[str]],
                      max_width: int = 100) -> List[str]:
    """
    Format data as a text table with proper alignment
    Returns list of formatted table lines
    """
    if not rows:
        return [f"No data to display"]

    # Calculate column widths
    col_widths = [len(header) for header in headers]

    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Adjust for max width constraint
    total_width = sum(col_widths) + len(headers) * 3 + 1  # Account for separators
    if total_width > max_width:
        # Proportionally reduce column widths
        reduction_factor = max_width / total_width
        col_widths = [max(8, int(w * reduction_factor)) for w in col_widths]

    # Format table
    lines = []

    # Header
    header_line = "| " + " | ".join(
        header[:col_widths[i]].ljust(col_widths[i])
        for i, header in enumerate(headers)
    ) + " |"
    lines.append(header_line)

    # Separator
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    lines.append(separator)

    # Data rows
    for row in rows:
        row_line = "| " + " | ".join(
            str(row[i] if i < len(row) else "")[:col_widths[i]].ljust(col_widths[i])
            for i in range(len(headers))
        ) + " |"
        lines.append(row_line)

    return lines


def display_progress_bar(current: int, total: int, width: int = 50,
                         prefix: str = "Progress") -> str:
    """
    Generate a text progress bar
    Returns formatted progress bar string
    """
    if total <= 0:
        return f"{prefix}: N/A"

    progress = current / total
    filled_width = int(width * progress)

    bar = "█" * filled_width + "░" * (width - filled_width)
    percentage = progress * 100

    return f"{prefix}: |{bar}| {percentage:.1f}% ({current}/{total})"


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """Flatten a nested list into a single list"""
    return [item for sublist in nested_list for item in sublist]


def remove_duplicates(data: List[Any], key_func: callable = None) -> List[Any]:
    """
    Remove duplicates from list, optionally using a key function
    """
    if key_func is None:
        return list(dict.fromkeys(data))  # Preserves order
    else:
        seen = set()
        result = []
        for item in data:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result


def generate_team_credentials(team_name: str) -> Dict[str, str]:
    """
    Generate username and password for a team
    Returns dict with 'username' and 'password'
    """
    from utils.validators import TeamValidator

    username = TeamValidator.generate_username(team_name)
    password = TeamValidator.generate_password(team_name)

    return {
        'username': username,
        'password': password
    }


def batch_process_with_progress(items: List[Any], process_func: callable,
                                batch_size: int = 10,
                                progress_callback: callable = None) -> Tuple[List[Any], List[str]]:
    """
    Process items in batches with optional progress tracking
    Returns (successful_results, error_messages)
    """
    results = []
    errors = []
    total = len(items)

    batches = chunk_list(items, batch_size)

    for batch_num, batch in enumerate(batches):
        for item_num, item in enumerate(batch):
            try:
                result = process_func(item)
                results.append(result)
            except Exception as e:
                errors.append(f"Error processing item {item}: {e}")

            # Progress callback
            if progress_callback:
                current = batch_num * batch_size + item_num + 1
                progress_callback(current, total)

    return results, errors


def validate_database_connection_params(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate database connection parameters
    Returns (is_valid, error_messages)
    """
    errors = []
    required_params = ['host', 'port', 'user', 'password', 'database']

    for param in required_params:
        if param not in params or not params[param]:
            errors.append(f"Missing required parameter: {param}")

    # Validate port is numeric
    if 'port' in params:
        try:
            port = int(params['port'])
            if port < 1 or port > 65535:
                errors.append("Port must be between 1 and 65535")
        except (ValueError, TypeError):
            errors.append("Port must be a valid number")

    return len(errors) == 0, errors


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Get file information including size, modified date, etc.
    Returns dict with file info or None if file doesn't exist
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None

        stat = path.stat()
        return {
            'name': path.name,
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'modified_formatted': format_datetime(datetime.fromtimestamp(stat.st_mtime)),
            'is_file': path.is_file(),
            'is_directory': path.is_dir(),
            'extension': path.suffix.lower()
        }
    except Exception as e:
        print(f"Error getting file info for {file_path}: {e}")
        return None