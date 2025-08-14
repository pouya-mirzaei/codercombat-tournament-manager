"""
Setup Menu for CoderCombat Tournament Management
Handles database setup, team management, and contest configuration
"""

import pymysql
from core import DatabaseManager
from config import DB_CONFIG, MESSAGES, TOURNAMENT_CONFIG


class SetupMenu:
    """Handles all setup and configuration menu operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

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
        """Team management submenu - placeholder for Step 2"""
        self._display_header()
        print("\n👥 Team Management")
        print("═" * 20)
        print(f"{MESSAGES['not_implemented']}")
        print("\nComing in Step 2:")
        print("• 📄 Load teams from CSV")
        print("• 👤 Create DOMjudge users for teams")
        print("• 📋 View all teams")
        print("• ✅ Verify team setup")

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
        print(f"Host: {self.db_manager.config['host']}")
        print(f"Database: {self.db_manager.config['database']}")

        if self.db_manager.connect():
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
                if choice in [str(c) for c in valid_choices]:
                    return choice
                print(f"{MESSAGES['invalid_choice']} Valid options: {valid_choices}")
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
        try:
            response = input(f"\n{message} [y/N]: ").strip().lower()
            return response in ['y', 'yes']
        except KeyboardInterrupt:
            print(f"\n{MESSAGES['goodbye']}")
            raise