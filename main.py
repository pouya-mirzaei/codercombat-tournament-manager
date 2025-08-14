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


from tests.validators import TestCSVValidator

test = TestCSVValidator()
# print(test.validate("data/teams.csv"))
# print(test.headersMatch("data/teams.csv" , ["name","email" , "institution"]))
print(TestCSVValidator.validate_teams_csv("data/teams.csv"))

exit(0)

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