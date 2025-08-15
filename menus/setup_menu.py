"""
Setup Menu for CoderCombat Tournament Management
Handles database setup, team management, and contest configuration
"""

import pymysql
from typing import List, Dict, Any

from core import ContestManager
from core.database import DatabaseManager
from core.domjudge_api import DOMjudgeAPI
from core.domjudge_db import DOMjudgeDBManager
from core.contest_engine import ContestEngine
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
                print(display_progress_bar(cnt, len(valid_teams), 100, f"inserted {cnt}/{len(valid_teams)}"))

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

        if not self.domjudge_api.test_connection(True):
            print("❌ Could not connect to DOMjudge API. Please check configuration.")
            self._pause_for_user()
            return

        # Get teams without DOMjudge IDs
        teams_to_process = self.db_manager.fetch_query("SELECT * FROM teams WHERE domjudge_team_id IS NULL")
        if not teams_to_process:
            print("✅ All teams already have DOMjudge accounts.")
            self._pause_for_user()
            return

        print(f"Processing {len(teams_to_process)} teams to create DOMjudge accounts...")

        # Participant category group ID (3 = participants in standard DOMjudge setup)
        PARTICIPANT_GROUP_ID = "3"

        successful_count = 0
        failed_teams = []

        for i, team in enumerate(teams_to_process):
            username = TeamValidator.generate_username(team['name'])
            password = TeamValidator.generate_password(team['name'])

            print(f"Creating accounts for: {team['name']} (username: {username})")

            # Prepare team data
            team_data = {
                'id': team['id'],
                'icpc_id': team['id'],
                'name': team['name'],
                'display_name': team['name'],
                'label': username,
                'group_ids': [PARTICIPANT_GROUP_ID]
            }

            # Prepare user data
            user_data = {
                'username': username,
                'name': team['name'],
                'roles': ["team"],
                'password': password,
                'team_id': None,
            }

            # Create team in DOMjudge
            team_result = self.domjudge_api.create_team(team_data)
            if team_result is None:
                failed_teams.append({
                    'name': team['name'],
                    'error': 'Failed to create team in DOMjudge',
                    'step': 'team_creation'
                })
                print(f"  ❌ Failed to create team for {team['name']}")
                continue

            # Update user data with team ID
            user_data['team_id'] = team_result['id']

            # Create user in DOMjudge
            user_result = self.domjudge_api.create_user(user_data)
            if user_result is None:
                failed_teams.append({
                    'name': team['name'],
                    'error': 'Failed to create user in DOMjudge (team was created)',
                    'step': 'user_creation',
                    'domjudge_team_id': team_result['id']
                })
                print(f"  ❌ Failed to create user for {team['name']} (team created successfully)")
                continue

            # Update local database with DOMjudge IDs
            update_query = "UPDATE teams SET domjudge_team_id = %s, domjudge_user_id = %s WHERE id = %s"
            if not self.db_manager.execute_query(update_query, (team_result['id'], user_result['id'], team['id'])):
                failed_teams.append({
                    'name': team['name'],
                    'error': 'Failed to update local database (DOMjudge accounts created)',
                    'step': 'database_update',
                    'domjudge_team_id': team_result['id'],
                    'domjudge_user_id': user_result['id']
                })
                print(f"  ❌ Failed to update database for {team['name']} (DOMjudge accounts created)")
                continue

            successful_count += 1
            print(f"  ✅ Successfully created accounts for {team['name']}")

            # Show progress
            progress_msg = f"Progress: {i + 1}/{len(teams_to_process)} teams processed"
            print(display_progress_bar(i + 1, len(teams_to_process), 50, progress_msg))

        # Final results summary
        print(f"\n{'=' * 50}")
        print(f"🎉 Account Creation Complete")
        print(f"✅ Successfully created: {successful_count}/{len(teams_to_process)} accounts")

        if failed_teams:
            print(f"❌ Failed: {len(failed_teams)} accounts")
            print("\nFailed Teams Details:")
            for failure in failed_teams:
                print(f"  • {failure['name']}: {failure['error']}")
                if failure['step'] in ['user_creation', 'database_update']:
                    print(f"    Note: DOMjudge team ID {failure.get('domjudge_team_id')} was created")
        else:
            print("🎉 All accounts created successfully!")

        print(f"{'=' * 50}")
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
            print(
                f"❌ DOMjudge Accounts: {domjudge_accounts_count}/{teams_in_db} accounts created. Please run 'Create DOMjudge accounts'.")
            is_ready = False

        print("\n" + "=" * 50)
        if is_ready:
            print("🎉 Team setup is complete!")
        else:
            print("⚠️  Team setup is incomplete. Please complete the missing steps.")
        print("=" * 50)

        self._pause_for_user()

    def _contest_setup_menu(self):
        """Contest setup submenu - Main functionality + Testing"""
        while True:
            self._display_header()
            print("\n🏆 Contest Setup")
            print("═" * 20)

            # Show contest status
            try:
                contest_manager = ContestManager(self.db_manager)
                status = contest_manager.get_contest_creation_status()
                contest_engine = ContestEngine()
                summary = contest_engine.get_contest_summary()

                print(f"📊 Total contests planned: {summary['total_contests']}")
                print(
                    f"🏆 By type: Duels: {summary['by_type']['duel']}, Groups: {summary['by_type']['group']}, Speed: {summary['by_type']['speed']}")
                print(f"Status: {status['total_created']}/{status['total_planned']} contests created in DOMjudge")
                print()
            except Exception as e:
                print(f"❌ Status error: {e}")
                print()

            print("=" * 60)
            print("📋 MAIN FUNCTIONALITY")
            print("=" * 60)

            options = [
                "🏗️ Create All Contests in DOMjudge",
                "📊 View Contest Creation Status",
                "⚙️ Manage Contest Settings",
                "✅ Verify Contest Setup"
            ]

            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")

            print("\n" + "=" * 60)
            print("🧪 TESTING & VALIDATION")
            print("=" * 60)

            testing_options = [
                "🧪 Test Contest Structure Generation",
                "📋 View All Planned Contests",
                "🔍 Test Contest Flow Mapping",
                "✅ Validate Contest Structure",
                "🎯 Test Initial Team Placement"
            ]

            for i, option in enumerate(testing_options, 5):
                print(f"{i}. {option}")

            print(f"\n{len(options) + len(testing_options) + 1}. 🔙 Back to Setup Menu")

            choice = self._get_user_choice("Select option", list(range(1, len(options) + len(testing_options) + 2)))

            if choice == "1":
                self._create_all_contests()
            elif choice == "2":
                self._view_contest_creation_status()
            elif choice == "3":
                self._manage_contest_settings()
            elif choice == "4":
                self._verify_contest_setup()
            elif choice == "5":
                self._test_contest_generation()
            elif choice == "6":
                self._view_all_planned_contests()
            elif choice == "7":
                self._test_contest_flow_mapping()
            elif choice == "8":
                self._validate_contest_structure()
            elif choice == "9":
                self._test_initial_team_placement()
            elif choice == "10":
                break

    def _test_contest_generation(self):
        """Test contest generation for specific rounds"""
        self._display_header()
        print("\n🧪 Test Contest Generation")
        print("═" * 30)

        try:
            contest_engine = ContestEngine()

            # Test each round
            for round_num in range(1, 9):
                print(f"\n🏆 Round {round_num}:")
                contests = contest_engine.generate_round_contests(round_num)

                for contest in contests:
                    print(f"  • {contest['contest_name']}: {contest['contest_type']} "
                          f"({contest['max_teams']} teams, {contest['problems_count']} problems)")

                print(f"  Total: {len(contests)} contests")

            print(f"\n{'=' * 50}")
            print("✅ Contest generation test completed successfully!")

        except Exception as e:
            print(f"❌ Contest generation failed: {e}")
            import traceback
            traceback.print_exc()

        self._pause_for_user()

    def _view_all_planned_contests(self):
        """View all planned contests in a formatted table"""
        self._display_header()
        print("\n📋 All Planned Contests")
        print("═" * 25)

        try:
            contest_engine = ContestEngine()
            all_contests = contest_engine.generate_all_contests()

            print(f"{'Round':<6} {'Contest Name':<20} {'Type':<6} {'Teams':<6} {'Problems':<9} {'Duration'}")
            print("-" * 70)

            for contest in all_contests:
                print(f"{contest['round_number']:<6} "
                      f"{contest['contest_name']:<20} "
                      f"{contest['contest_type']:<6} "
                      f"{contest['max_teams']:<6} "
                      f"{contest['problems_count']:<9} "
                      f"{contest['duration_minutes']} min")

            print("-" * 70)
            print(f"Total contests: {len(all_contests)}")

            # Show summary by round
            summary = contest_engine.get_contest_summary()
            print(f"\n📊 Summary by round:")
            for round_num, count in summary['by_round'].items():
                print(f"  Round {round_num}: {count} contests")

        except Exception as e:
            print(f"❌ Failed to generate contest list: {e}")
            import traceback
            traceback.print_exc()

        self._pause_for_user()

    def _test_contest_flow_mapping(self):
        """Test contest flow mapping"""
        self._display_header()
        print("\n🔍 Test Contest Flow Mapping")
        print("═" * 30)

        try:
            contest_engine = ContestEngine()

            # Test specific contests flow
            test_contests = [
                "R1_Duel_01", "R1_Duel_12", "R1_Duel_24",
                "R2_Group_Losers", "R2_Duel_06",
                "R3_Duel_01", "R7_Duel_01", "R8_Final", "R1_Duel_23"
            ]

            for contest_name in test_contests:
                flow = contest_engine.get_contest_flow(contest_name)
                print(f"\n🏆 {contest_name}:")
                if flow:
                    for key, value in flow.items():
                        print(f"  • {key}: {value}")
                else:
                    print(f"  ❌ No flow mapping found!")

            print(f"\n{'=' * 50}")
            print("✅ Contest flow mapping test completed!")

        except Exception as e:
            print(f"❌ Contest flow mapping test failed: {e}")
            import traceback
            traceback.print_exc()

        self._pause_for_user()

    def _validate_contest_structure(self):
        """Validate the complete contest structure"""
        self._display_header()
        print("\n✅ Validate Contest Structure")
        print("═" * 30)

        try:
            contest_engine = ContestEngine()
            is_valid, errors = contest_engine.validate_contest_structure()

            if is_valid:
                print("🎉 Contest structure validation PASSED!")
                print("✅ All contests have proper flow mappings")
                print("✅ Team counts are consistent")
                print("✅ Contest structure is valid")
            else:
                print("❌ Contest structure validation FAILED!")
                print("\nErrors found:")
                for error in errors:
                    print(f"  • {error}")

            # Show summary
            summary = contest_engine.get_contest_summary()
            print(f"\n📊 Structure Summary:")
            print(f"  Total contests: {summary['total_contests']}")
            print(f"  Duels: {summary['by_type']['duel']}")
            print(f"  Groups: {summary['by_type']['group']}")
            print(f"  Speed: {summary['by_type']['speed']}")

        except Exception as e:
            print(f"❌ Validation failed with error: {e}")
            import traceback
            traceback.print_exc()

        self._pause_for_user()

    def _test_initial_team_placement(self):
        """Test initial team placement for Round 1"""
        self._display_header()
        print("\n🎯 Test Initial Team Placement")
        print("═" * 35)

        try:
            contest_engine = ContestEngine()
            placement = contest_engine.get_initial_team_placement()

            print("Initial team placement for Round 1:")
            print("-" * 40)

            for contest_name, teams in placement.items():
                print(f"{contest_name}: Team {teams[0]} vs Team {teams[1]}")

            print("-" * 40)
            print(f"Total teams placed: {sum(len(teams) for teams in placement.values())}")
            print(f"Expected: 48 teams")

            # Verify all teams 1-48 are placed exactly once
            all_placed_teams = []
            for teams in placement.values():
                all_placed_teams.extend(teams)

            all_placed_teams.sort()
            expected_teams = list(range(1, 49))

            if all_placed_teams == expected_teams:
                print("✅ All 48 teams placed correctly, no duplicates!")
            else:
                print("❌ Team placement error!")
                missing = set(expected_teams) - set(all_placed_teams)
                duplicates = [x for x in all_placed_teams if all_placed_teams.count(x) > 1]
                if missing:
                    print(f"  Missing teams: {missing}")
                if duplicates:
                    print(f"  Duplicate teams: {set(duplicates)}")

        except Exception as e:
            print(f"❌ Team placement test failed: {e}")
            import traceback
            traceback.print_exc()

        self._pause_for_user()

    def _create_all_contests(self):
        """Create all contests in DOMjudge - Main functionality"""
        self._display_header()
        print("\n🏗️ Create All Contests in DOMjudge")
        print("═" * 35)

        if not self.db_manager.is_connected():
            print("❌ Tournament database not connected. Please connect first.")
            self._pause_for_user()
            return

        try:
            contest_manager = ContestManager(self.db_manager)

            # Check current status
            status = contest_manager.get_contest_creation_status()
            if status['total_created'] > 0:
                print(f"⚠️ {status['total_created']} contests already exist in DOMjudge.")
                if not self._confirm_action("Continue and create remaining contests?"):
                    return

            # Get activation delay from user
            print(f"\nContest activation settings:")
            print(f"Activation delay determines when contests become visible to teams.")
            print(f"Default: 48 hours from now")

            delay_input = input("Enter activation delay in hours [48]: ").strip()
            try:
                activation_delay = int(delay_input) if delay_input else 48
            except ValueError:
                print("Invalid input, using default 48 hours")
                activation_delay = 48

            print(f"\n🚀 Creating contests with {activation_delay}h activation delay...")
            if not self._confirm_action("This will create all planned contests in DOMjudge. Continue?"):
                return

            # Create contests
            results = contest_manager.create_all_contests(activation_delay)

            # Display results
            print(f"\n{'=' * 60}")
            print(f"🎉 Contest Creation Results")
            print(f"{'=' * 60}")
            print(f"✅ Successfully created: {results['success_count']}/{results['total_contests']}")

            if results['failed_contests']:
                print(f"❌ Failed: {len(results['failed_contests'])}")
                print("\nFailed contests:")
                for failure in results['failed_contests']:
                    print(f"  • {failure['name']}: {failure['error']}")
                    if failure.get('domjudge_id'):
                        print(f"    (DOMjudge ID: {failure['domjudge_id']})")
            else:
                print("🎉 All contests created successfully!")

            if results['success_count'] > 0:
                print(f"\n💡 Next steps:")
                print(f"• Contests are created but not visible to teams yet")
                print(f"• Use 'Manage Contest Settings' to activate when ready")
                print(f"• Use 'Verify Contest Setup' to check everything")

        except Exception as e:
            print(f"❌ Contest creation failed: {e}")
            import traceback
            traceback.print_exc()

        self._pause_for_user()

    def _view_contest_creation_status(self):
        """View detailed contest creation status"""
        self._display_header()
        print("\n📊 Contest Creation Status")
        print("═" * 30)

        try:
            contest_manager = ContestManager(self.db_manager)
            status = contest_manager.get_contest_creation_status()

            # Summary
            print(f"📋 Summary:")
            print(f"  Total planned: {status['total_planned']}")
            print(f"  Total created: {status['total_created']}")
            print(f"  Missing: {len(status['missing_contests'])}")

            # By round breakdown
            print(f"\n📊 By Round:")
            print(f"{'Round':<8} {'Planned':<8} {'Created':<8} {'Missing':<8}")
            print("-" * 40)

            for round_num, data in status['by_round'].items():
                missing_count = len(data.get('missing', []))
                print(f"R{round_num:<7} {data['planned']:<8} {data['created']:<8} {missing_count:<8}")

            # Created contests details
            if status['created_contests']:
                print(f"\n✅ Created Contests:")
                print(f"{'Contest Name':<25} {'Round':<6} {'Type':<6} {'DOMjudge ID'}")
                print("-" * 60)
                for contest in status['created_contests'][:10]:  # Show first 10
                    print(f"{contest['name']:<25} R{contest['round']:<5} {contest['type']:<6} {contest['domjudge_id']}")

                if len(status['created_contests']) > 10:
                    print(f"... and {len(status['created_contests']) - 10} more")

            # Missing contests
            if status['missing_contests']:
                print(f"\n❌ Missing Contests:")
                for contest in status['missing_contests'][:5]:  # Show first 5
                    print(f"  • R{contest['round']}: {contest['name']} ({contest['type']})")

                if len(status['missing_contests']) > 5:
                    print(f"  ... and {len(status['missing_contests']) - 5} more")

        except Exception as e:
            print(f"❌ Failed to get status: {e}")
            import traceback
            traceback.print_exc()

        self._pause_for_user()

    def _manage_contest_settings(self):
        """Manage contest timing and activation settings"""
        self._display_header()
        print("\n⚙️ Manage Contest Settings")
        print("═" * 30)

        print(f"{MESSAGES['not_implemented']}")
        print("\nComing in Step 4:")
        print("• ⚡ Activate contests for team visibility")
        print("• 📅 Set contest start times")
        print("• ⏰ Bulk timing management")
        print("• 🔄 Update contest schedules")

        self._pause_for_user()

    def _verify_contest_setup(self):
        """Comprehensive contest setup verification"""
        self._display_header()
        print("\n✅ Verify Contest Setup")
        print("═" * 25)

        try:
            contest_manager = ContestManager(self.db_manager)
            is_complete, errors, status_info = contest_manager.verify_contest_setup()

            print("🔍 Checking contest setup...")
            print("-" * 40)

            # Contest creation check
            contests_status = status_info['contests_status']
            if contests_status['total_created'] == contests_status['total_planned']:
                print("✅ Contest Creation: All contests created")
            elif contests_status['total_created'] > 0:
                print(
                    f"⚠️ Contest Creation: {contests_status['total_created']}/{contests_status['total_planned']} created")
            else:
                print("❌ Contest Creation: No contests created")

            # Contest structure check
            if status_info['structure_valid']:
                print("✅ Contest Structure: Valid")
            else:
                print("❌ Contest Structure: Invalid")

            # DOMjudge database check
            try:
                test_manager = ContestManager(self.db_manager)
                if test_manager.domjudge_db.connect():
                    print("✅ DOMjudge Database: Connected")
                    test_manager.domjudge_db.disconnect()
                else:
                    print("❌ DOMjudge Database: Connection failed")
            except:
                print("❌ DOMjudge Database: Error")

            print("-" * 40)

            # Overall status
            if is_complete:
                print("🎉 Contest setup is COMPLETE!")
                print("✅ Ready for tournament operations")
            else:
                print("⚠️ Contest setup is INCOMPLETE")
                print("\nIssues found:")
                for error in errors:
                    print(f"  • {error}")

            # Show summary
            print(f"\n📊 Summary:")
            print(f"  Contests: {contests_status['total_created']}/{contests_status['total_planned']} created")
            if contests_status['missing_contests']:
                print(f"  Missing: {len(contests_status['missing_contests'])} contests")

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            import traceback
            traceback.print_exc()

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

        print(f"\n{'=' * 50}")
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

# !/usr/bin/env python3
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
