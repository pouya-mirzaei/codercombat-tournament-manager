"""
Setup Menu for CoderCombat Tournament Management
Handles database setup, team management, and contest configuration
"""

import pymysql
from typing import List, Dict, Any
from core.database import DatabaseManager
from core.domjudge_api import DOMjudgeAPI
from core.domjudge_db import DOMjudgeDBManager
from config import DB_CONFIG, MESSAGES, TOURNAMENT_CONFIG, DOMJUDGE_API_CONFIG
from utils.validators import InputValidator, CSVValidator, TeamValidator
from utils.helpers import validate_database_connection_params, read_csv_file, format_table_data, display_progress_bar


class SetupMenu:
    """Handles all setup and configuration menu operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.domjudge_db = DOMjudgeDBManager()
        self.domjudge_api = DOMjudgeAPI(DOMJUDGE_API_CONFIG)

    def show_menu(self):
        """Display setup menu and handle navigation"""
        while True:
            self._display_header()

            options = [
                "🗄️ Database Setup",
                "👥 Team Management",
                "🏆 Contest Setup",
                "✅ Verify Complete Setup"
            ]


            print(self.domjudge_api.verify_api_access())

            self._display_menu_options("📋 Setup & Configuration", options)
            choice = self._get_user_choice("Select option", [1, 2, 3, 4, 5])

            if choice == "1":
                self._database_setup_menu()
            elif choice == "2":
                self._team_management_menu()
            elif choice == "3":
                self._contest_setup_menu()
            elif choice == "4":
                self._verify_setup_menu()
            elif choice == "5":
                break  # Back to main menu

    def _database_setup_menu(self):
        """Database setup submenu"""
        while True:
            self._display_header()

            # Show connection status
            tournament_status = "🟢 Connected" if self.db_manager.is_connected() else "🔴 Disconnected"
            domjudge_status = "🟢 Available" if self._test_domjudge_connection(silent=True) else "🔴 Unavailable"

            print(f"\n🗄️ Database Setup")
            print("═" * 20)
            print(f"Tournament DB: {tournament_status}")
            print(f"DOMjudge DB: {domjudge_status}")
            print()

            options = [
                "🔌 Connect to Tournament Database",
                "🧪 Test DOMjudge Database Connection",
                "🔨 Initialize Tournament Tables",
                "📊 View Database Status"
            ]

            self._display_menu_options("Database Operations", options)
            choice = self._get_user_choice("Select option", [1, 2, 3, 4, 5])

            if choice == "1":
                self._connect_tournament_database()
            elif choice == "2":
                self._test_domjudge_connection()
            elif choice == "3":
                self._initialize_tournament_tables()
            elif choice == "4":
                self._show_database_status()
            elif choice == "5":
                break

    def _team_management_menu(self):
        """Team management submenu - Implements Step 2"""
        while True:
            self._display_header()
            print("\n👥 Team Management")
            print("═" * 20)

            # Show team status
            teams_in_db = self.db_manager.get_teams_count()
            domjudge_accounts_query = "SELECT COUNT(*) AS count FROM teams WHERE domjudge_team_id IS NOT NULL"
            domjudge_accounts = self.db_manager.fetch_one(domjudge_accounts_query)
            domjudge_accounts_count = domjudge_accounts['count'] if domjudge_accounts else 0
            
            print(f"Teams in DB: {teams_in_db}/{TOURNAMENT_CONFIG['total_teams']}")
            print(f"DOMjudge Accounts: {domjudge_accounts_count}/{teams_in_db}")

            options = [
                "📄 Load teams from CSV",
                "👤 Create DOMjudge users for teams",
                "📋 View all teams",
                "✅ Verify team setup"
            ]
            self._display_menu_options("Team Operations", options)
            choice = self._get_user_choice("Select option", [1, 2, 3, 4, 5])

            if choice == "1":
                self._load_teams_from_csv()
            elif choice == "2":
                self._create_domjudge_accounts()
            elif choice == "3":
                self._view_all_teams()
            elif choice == "4":
                self._verify_team_setup()
            elif choice == "5":
                break

    def _load_teams_from_csv(self):
        """Load teams from a CSV file into the tournament database"""
        self._display_header()
        print("\n📄 Load Teams from CSV")
        print("═" * 25)

        # Prompt for file path and validate
        file_path = input("Enter path to CSV file (e.g., data/teams.csv): ").strip()
        is_valid_path, path_error = InputValidator.validate_file_path(file_path)

        if not is_valid_path:
            print(f"❌ Invalid file path: {path_error}")
            self._pause_for_user()
            return
        
        # Validate CSV content
        is_valid, errors, valid_teams = CSVValidator.validate_teams_csv(file_path)

        if not is_valid:
            print("❌ CSV validation failed:")
            for error in errors:
                print(f"  - {error}")
            self._pause_for_user()
            return

        print(f"✅ CSV file validated successfully. Found {len(valid_teams)} valid teams.")
        if not self._confirm_action("This will delete existing teams and load new ones. Continue?"):
            print("Operation cancelled.")
            self._pause_for_user()
            return

        # Delete existing teams
        if not self.db_manager.execute_query("DELETE FROM teams"):
            print("❌ Failed to clear existing teams.")
            self._pause_for_user()
            return


        # Insert new teams
        insert_query = "INSERT INTO teams (name) VALUES (%s)"
        cnt = 0
        for team in valid_teams:
            cnt += 1
            params = (team['name'])
            self.db_manager.execute_query(insert_query, params)
            if cnt % 7 == 0 or cnt == len(valid_teams):
                print(display_progress_bar(cnt,len(valid_teams), 100 , f"inserted {cnt}/{len(valid_teams)}"))

        print(f"🎉 Successfully loaded {len(valid_teams)} teams from CSV.")
        self._pause_for_user()

    def _create_domjudge_accounts(self):
        """Create DOMjudge users/teams for all teams in the local database"""
        self._display_header()
        print("\n👤 Create DOMjudge Accounts")
        print("═" * 25)

        if not self.db_manager.is_connected():
            print("❌ Tournament database not connected. Please connect first.")
            self._pause_for_user()
            return
        
        if not self.domjudge_db.connect():
            print("❌ Could not connect to DOMjudge database. Please check configuration.")
            self.domjudge_db.disconnect()
            self._pause_for_user()
            return

        # Get teams without DOMjudge IDs
        teams_to_process = self.db_manager.fetch_query("SELECT * FROM teams WHERE domjudge_team_id IS NULL")
        if not teams_to_process:
            print("✅ All teams already have DOMjudge accounts.")
            self.domjudge_db.disconnect()
            self._pause_for_user()
            return

        print(f"Processing {len(teams_to_process)} teams to create DOMjudge accounts...")

        for i, team in enumerate(teams_to_process):
            username = TeamValidator.generate_username(team['name'])
            password = TeamValidator.generate_password(team['name'])
            
            # Create user and team in DOMjudge
            domjudge_data = self.domjudge_db.create_team_with_user(
                team_name=team['name'],
                username=username,
                email=team['email'],
                password=password
            )

            if domjudge_data:
                # Update local tournament database with new IDs
                update_query = "UPDATE teams SET domjudge_team_id = %s, domjudge_user_id = %s WHERE id = %s"
                self.db_manager.execute_query(update_query, (domjudge_data['team_id'], domjudge_data['user_id'], team['id']))

            print(display_progress_bar(i + 1, len(teams_to_process)))

        self.domjudge_db.disconnect()
        print(f"\n🎉 Finished creating DOMjudge accounts.")
        self._pause_for_user()

    def _view_all_teams(self):
        """Display a formatted list of all teams"""
        self._display_header()
        print("\n📋 All Teams")
        print("═" * 15)

        teams = self.db_manager.fetch_query("SELECT * FROM teams ORDER BY name")

        if not teams:
            print("No teams found in the database.")
            self._pause_for_user()
            return

        headers = ["ID", "Name", "DOMjudge ID", "DOMjudge User ID"]
        rows = [
            [
                team['id'],
                team['name'],
                team['domjudge_team_id'] or 'N/A',
                team['domjudge_user_id'] or 'N/A'
            ]
            for team in teams
        ]

        table_lines = format_table_data(headers, rows)
        for line in table_lines:
            print(line)
        
        self._pause_for_user()

    def _verify_team_setup(self):
        """Verify that team setup is complete"""
        self._display_header()
        print("\n✅ Team Setup Verification")
        print("═" * 25)

        is_ready = True
        
        # Check team count
        teams_in_db = self.db_manager.get_teams_count()
        expected_teams = TOURNAMENT_CONFIG['total_teams']
        if teams_in_db == expected_teams:
            print(f"✅ Team Count: {teams_in_db}/{expected_teams} loaded.")
        else:
            print(f"❌ Team Count: {teams_in_db}/{expected_teams} loaded. Please load teams from CSV.")
            is_ready = False

        # Check DOMjudge accounts
        domjudge_accounts_query = "SELECT COUNT(*) AS count FROM teams WHERE domjudge_team_id IS NOT NULL"
        domjudge_accounts = self.db_manager.fetch_one(domjudge_accounts_query)
        domjudge_accounts_count = domjudge_accounts['count'] if domjudge_accounts else 0
        
        if domjudge_accounts_count == teams_in_db and teams_in_db > 0:
            print(f"✅ DOMjudge Accounts: {domjudge_accounts_count} accounts created for {teams_in_db} teams.")
        else:
            print(f"❌ DOMjudge Accounts: {domjudge_accounts_count}/{teams_in_db} accounts created. Please run 'Create DOMjudge accounts'.")
            is_ready = False

        print("\n" + "=" * 50)
        if is_ready:
            print("🎉 Team setup is complete!")
        else:
            print("⚠️  Team setup is incomplete. Please complete the missing steps.")
        print("=" * 50)

        self._pause_for_user()

    def _contest_setup_menu(self):
        """Contest setup submenu - placeholder for Step 3"""
        self._display_header()
        print("\n🏆 Contest Setup")
        print("═" * 20)
        print(f"{MESSAGES['not_implemented']}")
        print("\nComing in Step 3:")
        print("• 🏗️ Create all contests in DOMjudge")
        print("• ⏰ Configure contest timing")
        print("• 📋 View contest structure")
        print("• ✅ Verify contest setup")

        self._pause_for_user()

    def _verify_setup_menu(self):
        """Verify complete setup"""
        self._display_header()
        print("\n✅ Setup Verification")
        print("═" * 20)

        # Check tournament database
        print("🔍 Checking tournament database...")
        if self.db_manager.is_connected():
            if self.db_manager.test_connection():
                print("  ✅ Tournament database: Connected and responsive")

                # Check tables
                state = self.db_manager.get_tournament_state()
                if state:
                    print("  ✅ Tournament tables: Initialized")
                    print(f"  📊 Current state: Round {state['current_round']}, Phase: {state['current_phase']}")
                else:
                    print("  ❌ Tournament tables: Not initialized")
            else:
                print("  ❌ Tournament database: Connection issues")
        else:
            print("  ❌ Tournament database: Not connected")

        # Check DOMjudge database
        print("\n🔍 Checking DOMjudge database...")
        if self._test_domjudge_connection(silent=True):
            print("  ✅ DOMjudge database: Connected and accessible")
        else:
            print("  ❌ DOMjudge database: Connection failed")

        # Check teams (placeholder)
        print("\n🔍 Checking teams...")
        team_count = self.db_manager.get_teams_count()
        expected_teams = TOURNAMENT_CONFIG['total_teams']
        if team_count == expected_teams:
            print(f"  ✅ Teams: {team_count}/{expected_teams} loaded")
        elif team_count > 0:
            print(f"  ⚠️ Teams: {team_count}/{expected_teams} loaded (incomplete)")
        else:
            print(f"  ❌ Teams: 0/{expected_teams} loaded (not started)")

        # Check contests (placeholder)
        print("\n🔍 Checking contests...")
        print("  🚧 Contest verification coming in Step 3")

        print(f"\n{'='*50}")
        overall_ready = (
            self.db_manager.is_connected() and
            self.db_manager.test_connection() and
            self.db_manager.get_tournament_state() is not None
        )

        if overall_ready:
            print("🎉 System ready for tournament setup!")
        else:
            print("⚠️  Setup incomplete. Please complete missing steps.")

        self._pause_for_user()

    def _connect_tournament_database(self):
        """Connect to tournament database"""
        print("\n🔌 Connecting to tournament database...")


        # Use helper to validate connection parameters before attempting
        is_valid, errors = validate_database_connection_params(self.db_manager.config)
        if not is_valid:
            print("❌ Invalid database configuration:")
            for error in errors:
                print(f"    - {error}")
            self._pause_for_user()
            return

        print(f"Host: {self.db_manager.config['host']}")
        print(f"Database: {self.db_manager.config['database']}")

        if self.db_manager.is_connected() or self.db_manager.connect():
            print(f"{MESSAGES['operation_success']}")
            if self.db_manager.test_connection():
                print("✅ Connection test passed")
            else:
                print("⚠️ Connected but test query failed")
        else:
            print(f"{MESSAGES['operation_failed']}")

        self._pause_for_user()

    def _test_domjudge_connection(self, silent: bool = False) -> bool:
        """Test DOMjudge database connection"""
        if not silent:
            print("\n🧪 Testing DOMjudge database connection...")
            print(f"Host: {DB_CONFIG['domjudge']['host']}")
            print(f"Database: {DB_CONFIG['domjudge']['database']}")

        try:
            domjudge_conn = pymysql.connect(**DB_CONFIG['domjudge'])

            # Test with a simple query
            with domjudge_conn.cursor() as cursor:
                cursor.execute("SELECT VERSION() as version")
                result = cursor.fetchone()

            domjudge_conn.close()

            if not silent:
                print("✅ DOMjudge database connection successful!")
                if result:
                    print(f"📊 MySQL Version: {result[0]}")

            return True

        except pymysql.Error as e:
            if not silent:
                print(f"❌ DOMjudge database connection failed: {e}")
            return False
        except Exception as e:
            if not silent:
                print(f"❌ Unexpected error: {e}")
            return False
        finally:
            if not silent:
                self._pause_for_user()

    def _initialize_tournament_tables(self):
        """Initialize tournament database tables"""
        print("\n🔨 Initializing tournament tables...")

        if not self.db_manager.is_connected():
            print("❌ Please connect to tournament database first!")
            self._pause_for_user()
            return

        # Confirm action
        if not self._confirm_action("This will create/update database tables. Continue?"):
            print("Operation cancelled.")
            self._pause_for_user()
            return

        if self.db_manager.initialize_database():
            print(f"\n{MESSAGES['operation_success']}")
            print("🎯 Tournament system is ready for team and contest setup!")
        else:
            print(f"\n{MESSAGES['operation_failed']}")

        self._pause_for_user()

    def _show_database_status(self):
        """Show detailed database status"""
        self._display_header()
        print("\n📊 Database Status Report")
        print("═" * 30)

        # Tournament database status
        print("\n🗄️ Tournament Database:")
        if self.db_manager.is_connected():
            print(f"  Status: ✅ Connected")
            print(f"  Host: {self.db_manager.config['host']}")
            print(f"  Database: {self.db_manager.config['database']}")

            # Get table information
            tables_info = self.db_manager.fetch_query("SHOW TABLES")
            if tables_info:
                print(f"  Tables: {len(tables_info)} found")
                for table in tables_info:
                    table_name = list(table.values())[0]
                    count_result = self.db_manager.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
                    count = count_result['count'] if count_result else 0
                    print(f"    • {table_name}: {count} records")
        else:
            print("  Status: ❌ Not connected")

        # DOMjudge database status
        print("\n🏛️ DOMjudge Database:")
        if self._test_domjudge_connection(silent=True):
            print("  Status: ✅ Accessible")
            print(f"  Host: {DB_CONFIG['domjudge']['host']}")
            print(f"  Database: {DB_CONFIG['domjudge']['database']}")
        else:
            print("  Status: ❌ Not accessible")

        self._pause_for_user()

    # Helper methods
    def _display_header(self):
        """Display section header"""
        width = 60
        separator = "=" * width
        print(f"\n{separator}")
        print("🏆 CoderCombat Tournament Management System".center(width))
        print(separator)

    def _display_menu_options(self, title: str, options: list):
        """Display menu options"""
        print(f"\n{title}")
        print("═" * len(title))
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        print(f"{len(options) + 1}. 🔙 Back")

    def _get_user_choice(self, prompt: str, valid_choices: list) -> str:
        """Get user choice with validation"""
        while True:
            try:
                choice = input(f"\n{prompt}: ").strip()
                is_valid, error_msg = InputValidator.validate_choice(choice, valid_choices)
                if is_valid:
                    return choice
                print(error_msg)
            except KeyboardInterrupt:
                print(f"\n{MESSAGES['goodbye']}")
                raise

    def _pause_for_user(self, message: str = "Press Enter to continue..."):
        """Pause for user input"""
        try:
            input(f"\n{message}")
        except KeyboardInterrupt:
            print(f"\n{MESSAGES['goodbye']}")
            raise

    def _confirm_action(self, message: str) -> bool:
        """Get user confirmation"""
        while True:
            response = input(f"\n{message} [y/N]: ").strip()
            is_valid, is_yes, error_msg = InputValidator.validate_yes_no(response)
            if is_valid:
                return is_yes
            
            # Handle empty response with default value
            if not response:
                return False

            print(error_msg)

# File: main.py

#!/usr/bin/env python3
"""
CoderCombat Tournament Management System
Main entry point for the tournament management application

Usage:
    python main.py

This script provides an interactive console interface for managing
CoderCombat programming contests with DOMjudge integration.
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from menus.menu_system import MenuSystem
from config import MESSAGES


def check_dependencies():
    """Check if required dependencies are installed"""
    required_modules = ['pymysql', 'requests']
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print("❌ Missing required dependencies:")
        for module in missing_modules:
            print(f"   • {module}")
        print("\n💡 Install dependencies with:")
        print("   pip install -r requirements.txt")
        return False

    return True


def display_startup_banner():
    """Display application startup banner"""
    banner = f"""
{'=' * 60}
🏆 CoderCombat Tournament Management System
{'=' * 60}
Version: 1.0.0 (Step 1 - Foundation)
Author: Pouya Mirzaei
Description: Manage complex 8-round tournaments with DOMjudge
{'=' * 60}
"""
    print(banner)


def main():
    """Main entry point for the application"""
    try:
        # Display startup information
        display_startup_banner()

        # Check dependencies
        print("🔍 Checking system dependencies...")
        if not check_dependencies():
            sys.exit(1)
        print("✅ All dependencies available")

        # Initialize and run menu system
        print("🚀 Starting tournament management system...")
        menu_system = MenuSystem()
        menu_system.run()

    except KeyboardInterrupt:
        print(f"\n{MESSAGES['goodbye']}")
        sys.exit(0)

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure you're running from the project root directory:")
        print("   cd codercombat-tournament")
        print("   python main.py")
        sys.exit(1)

    except Exception as e:
        print(f"💥 Fatal error: {e}")
        print("\n🐛 This is unexpected. Please report this error.")
        sys.exit(1)


if __name__ == "__main__":
    main()