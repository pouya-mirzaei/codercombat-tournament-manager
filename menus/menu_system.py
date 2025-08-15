"""
Main Menu System for CoderCombat Tournament Management
Handles navigation and display logic
"""

import sys
from typing import List, Optional
from core import DatabaseManager
from config import DB_CONFIG, MENU_CONFIG, MESSAGES, TOURNAMENT_CONFIG
from utils.validators import InputValidator


class MenuSystem:
    """Main interactive console menu system"""

    def __init__(self):
        self.db_manager = DatabaseManager(DB_CONFIG['tournament'])
        self.tournament_started = False

    def display_header(self):
        """Display system header with current tournament state"""
        width = MENU_CONFIG['header_width']
        separator = MENU_CONFIG['separator_char'] * width

        print(f"\n{separator}")
        print(f"{MESSAGES['welcome']:^{width}}")
        print(separator)

        # Display tournament state if connected and configured
        if MENU_CONFIG['show_state_info'] and self.db_manager.is_connected():
            state = self._get_tournament_state_display()
            if state:
                print(state)
                print(separator)
        else:
            print("State: Database Not Connected".center(width))
            print(separator)

    def _get_tournament_state_display(self) -> Optional[str]:
        """Get formatted tournament state for display"""
        try:
            state = self.db_manager.get_tournament_state()
            if state:
                phase_display = state['current_phase'].replace('_', ' ').title()
                state_line = f"Current State: Round {state['current_round']} - {phase_display}"

                # Get team counts
                team_count = self.db_manager.get_teams_count()

                # Get teams with DOMjudge accounts
                domjudge_query = "SELECT COUNT(*) as count FROM teams WHERE domjudge_team_id IS NOT NULL"
                domjudge_result = self.db_manager.fetch_one(domjudge_query)
                domjudge_count = domjudge_result['count'] if domjudge_result else 0

                teams_line = (
                    f"Teams: {team_count}/{TOURNAMENT_CONFIG['total_teams']} loaded | "
                    f"DOMjudge: {domjudge_count}/{team_count} accounts"
                )

                return f"{state_line}\n{teams_line}"
            else:
                return "State: System Not Initialized"
        except Exception as e:
            return f"State: Error retrieving state - {e}"

    def get_user_choice(self, prompt: str, valid_choices: List[int], allow_back: bool = False) -> str:
        """Get and validate user input"""
        all_valid_choices = valid_choices[:]
        valid_str_choices = [str(c) for c in valid_choices]

        if allow_back:
            valid_str_choices.append('b')
            prompt += " (b for back)"

        while True:
            try:
                choice = input(f"\n{prompt}: ").strip().lower()

                if choice == 'b' and allow_back:
                    return choice
                if choice in ['q', 'quit', 'exit']:
                    self.cleanup_and_exit()

                # Validate numerical choice
                is_valid, error_msg = InputValidator.validate_choice(choice, all_valid_choices)
                if is_valid:
                    return choice
                else:
                    print(f"❌ {error_msg}")
                    if allow_back:
                        print("Enter 'b' to go back, 'q' to quit")
            except KeyboardInterrupt:
                print(f"\n{MESSAGES['goodbye']}")
                self.cleanup_and_exit()

    def display_menu_options(self, title: str, options: List[str], show_back: bool = True):
        """Display menu options with consistent formatting"""
        print(f"\n{title}")
        print("═" * len(title))

        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")

        if show_back:
            print(f"{len(options) + 1}. 🔙 Back to Previous Menu")

    def pause_for_user(self, message: str = "Press Enter to continue..."):
        """Pause execution and wait for user input"""
        try:
            input(f"\n{message}")
        except KeyboardInterrupt:
            print(f"\n{MESSAGES['goodbye']}")
            self.cleanup_and_exit()

    def confirm_action(self, message: str, default_yes: bool = False) -> bool:
        """Get user confirmation for dangerous operations"""
        suffix = " [Y/n]" if default_yes else " [y/N]"
        prompt = f"{message}{suffix}"

        while True:
            response = input(f"\n{prompt}: ").strip()
            is_valid, is_yes, error_msg = InputValidator.validate_yes_no(response)
            if is_valid:
                return is_yes

            # Handle empty response with default value
            if not response:
                return default_yes

            print(error_msg)

    def main_menu(self):
        """Display and handle main menu navigation"""
        while True:
            self.display_header()

            options = [
                "📋 Setup & Configuration",
                "🎮 Tournament Control",
                "📊 Monitoring & Reports",
                "🔧 System Tools",
                "🚪 Exit"
            ]

            self.display_menu_options("Main Menu", options, show_back=False)
            choice = self.get_user_choice("Select option", [1, 2, 3, 4, 5])

            if choice == "1":
                self._setup_menu()
            elif choice == "2":
                self._tournament_control_menu()
            elif choice == "3":
                self._monitoring_menu()
            elif choice == "4":
                self._system_tools_menu()
            elif choice == "5":
                self.cleanup_and_exit()

    def _setup_menu(self):
        """Setup and configuration menu"""
        # Import here to avoid circular imports
        from .setup_menu import SetupMenu
        setup_menu = SetupMenu(self.db_manager)
        setup_menu.show_menu()

    def _tournament_control_menu(self):
        """Tournament control menu - enhanced for Step 3"""
        self.display_header()
        print("\n🎮 Tournament Control")
        print("═" * 25)

        # Show current tournament readiness
        if self.db_manager.is_connected():
            state = self.db_manager.get_tournament_state()
            team_count = self.db_manager.get_teams_count()
            expected_teams = TOURNAMENT_CONFIG['total_teams']

            if state and team_count == expected_teams:
                print("✅ System Status: Ready for tournament operations")
                print(f"📊 Current Phase: {state['current_phase'].replace('_', ' ').title()}")
                print(f"🏆 Round: {state['current_round']}")
                print()

                # Show available options based on current state
                if state['current_phase'] == 'setup':
                    print("🚧 Available Operations:")
                    print("• Contest creation and setup (Step 3)")
                    print("• Tournament initialization")
                elif state['current_phase'] == 'round_active':
                    print("🚧 Available Operations:")
                    print("• Monitor active contests")
                    print("• Check contest status")
                else:
                    print("🚧 Available Operations:")
                    print("• Process round results")
                    print("• Advance teams to next round")
            else:
                print("⚠️ System Status: Setup incomplete")
                if team_count != expected_teams:
                    print(f"❌ Teams: {team_count}/{expected_teams} loaded")
                print("💡 Please complete Setup & Configuration first")
        else:
            print("❌ System Status: Database not connected")

        print(f"\n{MESSAGES['not_implemented']}")
        print("\nComing in Step 4:")
        print("• ▶️  Start Tournament (Round 1)")
        print("• 📊 Process Round Results")
        print("• ✅ Activate Next Round")
        print("• 🔍 Check Contest Status")
        print("• ⚙️  Manual Adjustments")
        print("• 📈 View Tournament Brackets")

        self.pause_for_user()

    def _monitoring_menu(self):
        """Monitoring and reports menu - enhanced status display"""
        self.display_header()
        print("\n📊 Monitoring & Reports")
        print("═" * 25)

        # Show current system status
        if self.db_manager.is_connected():
            print("📈 System Status Overview:")
            print("-" * 30)

            # Tournament database status
            state = self.db_manager.get_tournament_state()
            if state:
                print(f"🎯 Tournament Phase: {state['current_phase'].replace('_', ' ').title()}")
                print(f"🏆 Current Round: {state['current_round']}")

            # Team statistics
            team_count = self.db_manager.get_teams_count()
            expected_teams = TOURNAMENT_CONFIG['total_teams']
            print(f"👥 Teams Loaded: {team_count}/{expected_teams}")

            # DOMjudge accounts
            domjudge_query = "SELECT COUNT(*) as count FROM teams WHERE domjudge_team_id IS NOT NULL"
            result = self.db_manager.fetch_one(domjudge_query)
            domjudge_count = result['count'] if result else 0
            print(f"🔗 DOMjudge Accounts: {domjudge_count}/{team_count}")

            # Contest status (placeholder for Step 3)
            print(f"🏆 Contests Created: 0/TBD (Step 3)")

            print("-" * 30)
        else:
            print("❌ Cannot display status: Database not connected")

        print(f"\n{MESSAGES['not_implemented']}")
        print("\nComing in Step 5:")
        print("• 📊 Live tournament status")
        print("• 🏆 Contest monitoring dashboard")
        print("• 👥 Team performance reports")
        print("• 📈 Tournament analytics")
        print("• ⚡ Real-time contest updates")

        self.pause_for_user()

    def _system_tools_menu(self):
        """System tools menu - enhanced with actual tools"""
        self.display_header()
        print("\n🔧 System Tools")
        print("═" * 20)

        # Show quick system diagnostics
        print("🔍 Quick System Diagnostics:")
        print("-" * 35)

        # Tournament DB status
        if self.db_manager.is_connected():
            print("✅ Tournament Database: Connected")
            if self.db_manager.test_connection():
                print("✅ Tournament DB Test: Passed")
            else:
                print("❌ Tournament DB Test: Failed")
        else:
            print("❌ Tournament Database: Not Connected")

        # DOMjudge DB status (test connection)
        try:
            from core import DOMjudgeDBManager
            domjudge_db = DOMjudgeDBManager()
            if domjudge_db.connect():
                print("✅ DOMjudge Database: Accessible")
                domjudge_db.disconnect()
            else:
                print("❌ DOMjudge Database: Connection Failed")
        except Exception as e:
            print(f"❌ DOMjudge Database: Error ({str(e)[:30]}...)")

        # DOMjudge API status
        try:
            from core.domjudge_api import DOMjudgeAPI
            api = DOMjudgeAPI()
            if api.test_connection():
                print("✅ DOMjudge API: Accessible")
            else:
                print("❌ DOMjudge API: Connection Failed")
        except Exception as e:
            print(f"❌ DOMjudge API: Error ({str(e)[:30]}...)")

        print("-" * 35)

        print(f"\n{MESSAGES['not_implemented']}")
        print("\nComing in Step 6:")
        print("• 🗄️ Database backup/restore utilities")
        print("• 🔄 DOMjudge synchronization tools")
        print("• 🐛 Debug utilities and diagnostics")
        print("• 📊 System performance monitoring")
        print("• 🔧 Configuration management")

        self.pause_for_user()

    def cleanup_and_exit(self):
        """Clean up resources and exit gracefully"""
        print(f"\n🧹 Cleaning up...")
        if self.db_manager:
            self.db_manager.disconnect()
        print(f"{MESSAGES['goodbye']}")
        sys.exit(0)

    def run(self):
        """Main entry point for the menu system"""
        try:
            # Attempt to connect to the tournament database at startup
            self.db_manager.connect()
            self.main_menu()
        except KeyboardInterrupt:
            print(f"\n{MESSAGES['goodbye']}")
            self.cleanup_and_exit()
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            if self.db_manager:
                self.db_manager.disconnect()
            sys.exit(1)