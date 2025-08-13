"""
Main Menu System for CoderCombat Tournament Management
Handles navigation and display logic
"""

import sys
from typing import List, Optional
from core import DatabaseManager
from config import DB_CONFIG, MENU_CONFIG, MESSAGES, TOURNAMENT_CONFIG


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

                teams_line = (
                    f"Winners: {state['winners_league_count']} | "
                    f"Losers: {state['losers_league_count']} | "
                    f"Eliminated: {state['eliminated_count']}"
                )

                return f"{state_line}\n{teams_line}"
            else:
                return "State: System Not Initialized"
        except Exception as e:
            return f"State: Error retrieving state - {e}"

    def get_user_choice(self, prompt: str, valid_choices: List[int], allow_back: bool = False) -> str:
        """Get and validate user input"""
        valid_str_choices = [str(c) for c in valid_choices]
        if allow_back:
            valid_str_choices.append('b')
            prompt += " (b for back)"

        while True:
            try:
                choice = input(f"\n{prompt}: ").strip().lower()
                if choice in valid_str_choices:
                    return choice
                elif choice in ['q', 'quit', 'exit']:
                    self.cleanup_and_exit()
                else:
                    print(f"{MESSAGES['invalid_choice']} Valid options: {valid_choices}")
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

        try:
            response = input(f"\n{prompt}: ").strip().lower()
            if not response:
                return default_yes
            return response in ['y', 'yes', 'true', '1']
        except KeyboardInterrupt:
            print(f"\n{MESSAGES['goodbye']}")
            self.cleanup_and_exit()

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
        """Tournament control menu - placeholder for future implementation"""
        self.display_header()
        print("\n🎮 Tournament Control")
        print("═" * 25)
        print(f"{MESSAGES['not_implemented']}")
        print("\nThis section will include:")
        print("• ▶️  Start Tournament (Round 1)")
        print("• 📊 Process Round Results")
        print("• ✅ Activate Next Round")
        print("• 🔍 Check Contest Status")
        print("• ⚙️  Manual Adjustments")
        print("• 📈 View Tournament Brackets")

        self.pause_for_user()

    def _monitoring_menu(self):
        """Monitoring and reports menu - placeholder"""
        self.display_header()
        print("\n📊 Monitoring & Reports")
        print("═" * 25)
        print(f"{MESSAGES['not_implemented']}")
        print("\nThis section will include:")
        print("• Live tournament status")
        print("• Contest monitoring")
        print("• Team performance reports")
        print("• Tournament analytics")

        self.pause_for_user()

    def _system_tools_menu(self):
        """System tools menu - placeholder"""
        self.display_header()
        print("\n🔧 System Tools")
        print("═" * 20)
        print(f"{MESSAGES['not_implemented']}")
        print("\nThis section will include:")
        print("• Database maintenance")
        print("• DOMjudge integration tools")
        print("• Debug utilities")
        print("• System diagnostics")

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
            self.main_menu()
        except KeyboardInterrupt:
            print(f"\n{MESSAGES['goodbye']}")
            self.cleanup_and_exit()
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            if self.db_manager:
                self.db_manager.disconnect()
            sys.exit(1)