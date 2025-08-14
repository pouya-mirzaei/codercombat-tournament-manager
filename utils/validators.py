"""
Input Validation Utilities
Provides validation functions for team data, contest parameters, and user inputs
"""

import re
import csv
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason}")


class TeamValidator:
    """Validates team-related data"""

    @staticmethod
    def validate_team_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate team name
        Returns (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Team name cannot be empty"

        name = name.strip()

        # Length check
        if len(name) < 2:
            return False, "Team name must be at least 2 characters"
        if len(name) > 100:
            return False, "Team name must be less than 100 characters"

        # Character check - allow alphanumeric, spaces, and common symbols
        if not re.match(r'^[a-zA-Z0-9\s\-_\.()]+$', name):
            return False, "Team name contains invalid characters (only letters, numbers, spaces, -, _, ., () allowed)"

        # No leading/trailing spaces or special chars
        if name != name.strip():
            return False, "Team name cannot start or end with spaces"

        return True, None

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address
        Returns (is_valid, error_message)
        """
        if not email or not email.strip():
            return False, "Email cannot be empty"

        email = email.strip().lower()

        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            return False, "Invalid email format"

        if len(email) > 255:
            return False, "Email too long (max 255 characters)"

        return True, None

    @staticmethod
    def validate_institution(institution: str) -> Tuple[bool, Optional[str]]:
        """
        Validate institution name
        Returns (is_valid, error_message)
        """
        if not institution or not institution.strip():
            return False, "Institution cannot be empty"

        institution = institution.strip()

        if len(institution) < 2:
            return False, "Institution name must be at least 2 characters"
        if len(institution) > 200:
            return False, "Institution name must be less than 200 characters"

        return True, None

    @staticmethod
    def generate_username(team_name: str) -> str:
        """
        Generate a username from team name
        Returns a safe username for DOMjudge
        """
        # Convert to lowercase, replace spaces and special chars with underscores
        username = re.sub(r'[^a-zA-Z0-9]', '_', team_name.lower())

        # Remove multiple consecutive underscores
        username = re.sub(r'_+', '_', username)

        # Remove leading/trailing underscores
        username = username.strip('_')

        # Ensure minimum length
        if len(username) < 3:
            username = f"team_{username}"

        # Ensure maximum length
        if len(username) > 50:
            username = username[:50]

        return username

    @staticmethod
    def generate_password(team_name: str, length: int = 12) -> str:
        """
        Generate a secure password for a team
        Returns a password based on team name with added security
        """
        import hashlib
        import secrets

        # Create a hash of the team name for consistency
        name_hash = hashlib.md5(team_name.encode()).hexdigest()[:8]

        # Add random component for security
        random_part = secrets.token_urlsafe(4)

        # Combine and ensure proper length
        password = f"{name_hash}{random_part}"

        if len(password) > length:
            password = password[:length]
        elif len(password) < length:
            # Pad with random characters if needed
            additional = secrets.token_urlsafe(length - len(password))
            password += additional[:length - len(password)]

        return password

    @staticmethod
    def validate_team_data(team_data: Dict) -> Dict[str, Optional[str]]:
        """
        Validate complete team data dictionary
        Returns dict of field_name -> error_message (None if valid)
        """
        errors = {}

        # Validate team name
        if 'name' in team_data:
            is_valid, error = TeamValidator.validate_team_name(team_data['name'])
            errors['name'] = error
        else:
            errors['name'] = "Team name is required"

        # Validate email
        if 'email' in team_data:
            is_valid, error = TeamValidator.validate_email(team_data['email'])
            errors['email'] = error
        else:
            errors['email'] = "Email is required"

        # Validate institution
        if 'institution' in team_data:
            is_valid, error = TeamValidator.validate_institution(team_data['institution'])
            errors['institution'] = error
        else:
            errors['institution'] = "Institution is required"

        return errors


class CSVValidator:
    """Validates CSV files and data"""

    @staticmethod
    def validate_csv_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that CSV file exists and is readable
        Returns (is_valid, error_message)
        """
        path = Path(file_path)

        if not path.exists():
            return False, f"File does not exist: {file_path}"

        if not path.is_file():
            return False, f"Path is not a file: {file_path}"

        if path.suffix.lower() not in ['.csv', '.txt']:
            return False, f"File must be .csv or .txt format"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to read first few lines to check if it's readable
                for i, line in enumerate(f):
                    if i > 2:  # Check first 3 lines
                        break
                return True, None
        except UnicodeDecodeError:
            return False, "File encoding error - file must be UTF-8"
        except PermissionError:
            return False, "Permission denied - cannot read file"
        except Exception as e:
            return False, f"File read error: {e}"

    @staticmethod
    def validate_csv_headers(file_path: str, expected_headers: List[str]) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate CSV headers match expected format
        Returns (is_valid, error_message, actual_headers)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)

                # Clean headers (strip whitespace, lowercase)
                clean_headers = [h.strip().lower() for h in headers]
                expected_clean = [h.strip().lower() for h in expected_headers]

                if clean_headers != expected_clean:
                    return False, f"Headers mismatch. Expected: {expected_headers}, Got: {headers}", headers

                return True, None, headers

        except StopIteration:
            return False, "CSV file is empty", []
        except Exception as e:
            return False, f"Error reading CSV headers: {e}", []

    @staticmethod
    def validate_teams_csv(file_path: str) -> Tuple[bool, List[str], List[Dict]]:
        """
        Validate teams CSV file completely
        Returns (is_valid, error_messages, valid_teams)
        """
        errors = []
        valid_teams = []

        # Expected headers for teams CSV
        expected_headers = ['name', 'email', 'institution']

        # Check file exists and is readable
        file_valid, file_error = CSVValidator.validate_csv_file(file_path)
        if not file_valid:
            return False, [file_error], []

        # Check headers
        headers_valid, headers_error, actual_headers = CSVValidator.validate_csv_headers(file_path, expected_headers)
        if not headers_valid:
            errors.append(headers_error)
            return False, errors, []

        # Validate data rows
        seen_names = set()
        seen_emails = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # Start from 2 (after header)
                    row_errors = []

                    # Clean row data
                    team_data = {
                        'name': row.get('name', '').strip(),
                        'email': row.get('email', '').strip().lower(),
                        'institution': row.get('institution', '').strip()
                    }

                    # Validate individual fields
                    field_errors = TeamValidator.validate_team_data(team_data)
                    for field, error in field_errors.items():
                        if error:
                            row_errors.append(f"Row {row_num}, {field}: {error}")

                    # Check for duplicate team names
                    if team_data['name'] and team_data['name'] in seen_names:
                        row_errors.append(f"Row {row_num}: Duplicate team name '{team_data['name']}'")
                    else:
                        seen_names.add(team_data['name'])

                    # Check for duplicate emails
                    if team_data['email'] and team_data['email'] in seen_emails:
                        row_errors.append(f"Row {row_num}: Duplicate email '{team_data['email']}'")
                    else:
                        seen_emails.add(team_data['email'])

                    # If row has errors, add to error list; otherwise add to valid teams
                    if row_errors:
                        errors.extend(row_errors)
                    else:
                        # Add row number for tracking
                        team_data['row_number'] = row_num
                        valid_teams.append(team_data)

        except Exception as e:
            errors.append(f"Error reading CSV data: {e}")
            return False, errors, []

        # Check minimum team count
        if len(valid_teams) == 0:
            errors.append("No valid teams found in CSV file")

        # Return results
        is_valid = len(errors) == 0
        return is_valid, errors, valid_teams


class ContestValidator:
    """Validates contest-related data"""

    @staticmethod
    def validate_contest_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate contest name format
        Returns (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Contest name cannot be empty"

        name = name.strip()

        # Length check
        if len(name) < 3:
            return False, "Contest name must be at least 3 characters"
        if len(name) > 100:
            return False, "Contest name must be less than 100 characters"

        # Format check - allow alphanumeric, spaces, and common symbols
        if not re.match(r'^[a-zA-Z0-9\s\-_\.()]+$', name):
            return False, "Contest name contains invalid characters"

        return True, None

    @staticmethod
    def validate_round_number(round_num: int) -> Tuple[bool, Optional[str]]:
        """
        Validate tournament round number
        Returns (is_valid, error_message)
        """
        if not isinstance(round_num, int):
            return False, "Round number must be an integer"

        if round_num < 1 or round_num > 8:
            return False, "Round number must be between 1 and 8"

        return True, None

    @staticmethod
    def validate_contest_duration(duration_minutes: int) -> Tuple[bool, Optional[str]]:
        """
        Validate contest duration
        Returns (is_valid, error_message)
        """
        if not isinstance(duration_minutes, int):
            return False, "Duration must be an integer (minutes)"

        if duration_minutes < 30:
            return False, "Contest duration must be at least 30 minutes"
        if duration_minutes > 600:  # 10 hours max
            return False, "Contest duration must be less than 600 minutes (10 hours)"

        return True, None

    @staticmethod
    def validate_team_count(count: int, contest_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate team count for specific contest type
        Returns (is_valid, error_message)
        """
        if not isinstance(count, int):
            return False, "Team count must be an integer"

        if count < 1:
            return False, "Team count must be at least 1"

        # Contest type specific limits
        if contest_type == 'duel' and count != 2:
            return False, "Duel contests must have exactly 2 teams"
        elif contest_type == 'group' and count > 50:
            return False, "Group contests cannot have more than 50 teams"
        elif contest_type == 'speed' and count > 50:
            return False, "Speed contests cannot have more than 50 teams"

        return True, None


class InputValidator:
    """Validates user input from console menus"""

    @staticmethod
    def validate_choice(choice: str, valid_choices: List[int]) -> Tuple[bool, Optional[str]]:
        """
        Validate menu choice input
        Returns (is_valid, error_message)
        """
        if not choice:
            return False, "Choice cannot be empty"

        try:
            choice_int = int(choice)
            if choice_int in valid_choices:
                return True, None
            else:
                return False, f"Choice must be one of: {valid_choices}"
        except ValueError:
            return False, "Choice must be a number"

    @staticmethod
    def validate_yes_no(response: str) -> Tuple[bool, bool, Optional[str]]:
        """
        Validate yes/no response
        Returns (is_valid, is_yes, error_message)
        """
        if not response:
            return False, False, "Response cannot be empty"

        response = response.strip().lower()

        if response in ['y', 'yes', 'true', '1']:
            return True, True, None
        elif response in ['n', 'no', 'false', '0']:
            return True, False, None
        else:
            return False, False, "Please enter 'y' for yes or 'n' for no"

    @staticmethod
    def validate_file_path(path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file path input
        Returns (is_valid, error_message)
        """
        if not path or not path.strip():
            return False, "File path cannot be empty"

        path = path.strip()

        # Basic path validation
        try:
            path_obj = Path(path)
            # Check if it's a reasonable path format
            if len(str(path_obj)) > 500:
                return False, "File path too long"
            return True, None
        except Exception as e:
            return False, f"Invalid file path format: {e}"


# Utility functions for common validation tasks
def validate_team_list(teams: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Validate a list of team dictionaries
    Returns (valid_teams, error_messages)
    """
    valid_teams = []
    errors = []
    seen_names = set()
    seen_emails = set()

    for i, team in enumerate(teams):
        team_errors = TeamValidator.validate_team_data(team)
        row_errors = []

        for field, error in team_errors.items():
            if error:
                row_errors.append(f"Team {i+1}, {field}: {error}")

        # Check duplicates
        team_name = team.get('name', '').strip()
        team_email = team.get('email', '').strip().lower()

        if team_name in seen_names:
            row_errors.append(f"Team {i+1}: Duplicate team name '{team_name}'")
        else:
            seen_names.add(team_name)

        if team_email in seen_emails:
            row_errors.append(f"Team {i+1}: Duplicate email '{team_email}'")
        else:
            seen_emails.add(team_email)

        if row_errors:
            errors.extend(row_errors)
        else:
            valid_teams.append(team)

    return valid_teams, errors


def clean_csv_data(file_path: str) -> str:
    """
    Clean CSV file by removing empty lines and fixing common issues
    Returns path to cleaned file or original path if no changes needed
    """
    try:
        lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Skip empty lines and lines with only whitespace
                if line.strip():
                    lines.append(line)

        # If we removed lines, write to a temporary cleaned file
        if len(lines) != sum(1 for _ in open(file_path, 'r', encoding='utf-8')):
            cleaned_path = file_path.replace('.csv', '_cleaned.csv')
            with open(cleaned_path, 'w', encoding='utf-8', newline='') as f:
                f.writelines(lines)
            return cleaned_path
        else:
            return file_path

    except Exception as e:
        print(f"Warning: Could not clean CSV file: {e}")
        return file_path