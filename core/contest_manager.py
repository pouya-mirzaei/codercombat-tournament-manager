"""
Contest Manager - Sub-Step 3.2: DOMjudge Contest Creation
Handles contest creation via DOMjudge API and database synchronization
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from core.database import DatabaseManager
from core.domjudge_db import DOMjudgeDBManager
from core.domjudge_api import DOMjudgeAPI
from core.contest_engine import ContestEngine
from config import TABLE_NAMES


class ContestManager:
    """Manages contest creation and synchronization with DOMjudge"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.domjudge_db = DOMjudgeDBManager()
        self.domjudge_api = DOMjudgeAPI()
        self.contest_engine = ContestEngine()

    def create_all_contests(self, activation_delay_hours: int = 48) -> Dict[str, Any]:
        """
        Create all planned contests in DOMjudge with progress tracking.
        Returns: {success_count, failed_contests, total_contests}
        """
        print("🏗️ Creating all contests in DOMjudge...")

        # Get all planned contests
        all_contests = self.contest_engine.generate_all_contests()

        # Connect to DOMjudge database
        if not self.domjudge_db.connect():
            return {
                'success': False,
                'error': 'Failed to connect to DOMjudge database',
                'success_count': 0,
                'failed_contests': [],
                'total_contests': len(all_contests)
            }

        results = {
            'success_count': 0,
            'failed_contests': [],
            'total_contests': len(all_contests),
            'created_contests': []
        }

        try:
            for i, contest_data in enumerate(all_contests):
                print(f"\nCreating contest {i + 1}/{len(all_contests)}: {contest_data['contest_name']}")

                # Create contest in DOMjudge
                domjudge_contest_id = self._create_single_contest(contest_data, activation_delay_hours)

                if domjudge_contest_id:
                    # Set open_for_all_teams = 0
                    if self._set_contest_closed(domjudge_contest_id):
                        # Save to local database
                        if self._save_contest_to_db(contest_data, domjudge_contest_id):
                            results['success_count'] += 1
                            results['created_contests'].append({
                                'name': contest_data['contest_name'],
                                'domjudge_id': domjudge_contest_id
                            })
                            print(f"  ✅ Success: {contest_data['contest_name']} (ID: {domjudge_contest_id})")
                        else:
                            results['failed_contests'].append({
                                'name': contest_data['contest_name'],
                                'error': 'Failed to save to local database',
                                'domjudge_id': domjudge_contest_id
                            })
                            print(f"  ⚠️ Contest created in DOMjudge but failed to save locally")
                    else:
                        results['failed_contests'].append({
                            'name': contest_data['contest_name'],
                            'error': 'Failed to set contest as closed',
                            'domjudge_id': domjudge_contest_id
                        })
                        print(f"  ⚠️ Contest created but failed to set as closed")
                else:
                    results['failed_contests'].append({
                        'name': contest_data['contest_name'],
                        'error': 'Failed to create in DOMjudge',
                        'domjudge_id': None
                    })
                    print(f"  ❌ Failed to create {contest_data['contest_name']}")

                # Progress indicator
                progress = int((i + 1) / len(all_contests) * 50)
                bar = "█" * progress + "░" * (50 - progress)
                print(f"Progress: [{bar}] {i + 1}/{len(all_contests)}")
                


        finally:
            self.domjudge_db.disconnect()

        return results

    def _create_single_contest(self, contest_data: Dict[str, Any], activation_delay_hours: int) -> Optional[str]:
        """
        Create a single contest in DOMjudge using the DOMjudgeAPI class.
        Returns DOMjudge contest ID or None if failed.
        """
        # Calculate activation and start times
        activation_time = datetime.now() + timedelta(hours=activation_delay_hours)

        start_time = activation_time + timedelta(hours=1)  # Default: start 1 hour after activation

        # Format duration as H:MM:SS
        duration_minutes = contest_data['duration_minutes']
        duration_hours = duration_minutes // 60
        duration_mins = duration_minutes % 60
        duration_str = f"{duration_hours}:{duration_mins:02d}:00"

        # Prepare contest JSON data
        contest_json = {
            "short_name": contest_data['contest_name'],
            "name": f"{contest_data['contest_name']} - {contest_data['contest_type'].title()}",
            "activation_time": activation_time.strftime("%Y-%m-%d %H:%M:%S Asia/Tehran"),
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S Asia/Tehran"),
            "duration": duration_str,
        }

        try:
            # Use DOMjudgeAPI to create contest with form-data
            # We need to add this method to DOMjudgeAPI class
            contest_id_array = self.domjudge_api.create_contest_with_json(contest_json)
            return contest_id_array

        except Exception as e:
            print(f"  ❌ Contest creation failed: {e}")
            return None

    def _set_contest_closed(self, domjudge_contest_id: str) -> bool:
        """Set contest open_for_all_teams = 0 using DOMjudge database"""
        try:
            query = "UPDATE contest SET open_to_all_teams = 0 WHERE cid = %s"
            return self.domjudge_db.execute_query(query, (domjudge_contest_id,))
        except Exception as e:
            print(f"  ❌ Failed to set contest as closed: {e}")
            return False

    def _save_contest_to_db(self, contest_data: Dict[str, Any], domjudge_contest_id: str) -> bool:
        """Save contest information to local tournament database"""
        try:
            query = f"""
            INSERT INTO {TABLE_NAMES['contests']} 
            (contest_name, round_number, contest_type, domjudge_contest_id, max_teams, problems_count)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            params = (
                contest_data['contest_name'],
                contest_data['round_number'],
                contest_data['contest_type'],
                int(domjudge_contest_id),
                contest_data['max_teams'],
                contest_data['problems_count']
            )

            return self.db_manager.execute_query(query, params)

        except Exception as e:
            print(f"  ❌ Failed to save contest to local DB: {e}")
            return False

    def get_contest_creation_status(self) -> Dict[str, Any]:
        """
        Get status of contest creation comparing planned vs created contests.
        Returns detailed status information.
        """
        # Get planned contests
        planned_contests = self.contest_engine.generate_all_contests()

        # Get created contests from local database
        created_contests_query = f"""
        SELECT contest_name, round_number, contest_type, domjudge_contest_id, max_teams, problems_count
        FROM {TABLE_NAMES['contests']}
        ORDER BY round_number, contest_name
        """
        created_contests = self.db_manager.fetch_query(created_contests_query) or []

        # Create status mapping
        created_names = {contest['contest_name']: contest for contest in created_contests}

        status_data = {
            'total_planned': len(planned_contests),
            'total_created': len(created_contests),
            'missing_contests': [],
            'created_contests': [],
            'by_round': {}
        }

        # Analyze each planned contest
        for planned in planned_contests:
            round_num = planned['round_number']
            if round_num not in status_data['by_round']:
                status_data['by_round'][round_num] = {
                    'planned': 0, 'created': 0, 'missing': []
                }

            status_data['by_round'][round_num]['planned'] += 1

            if planned['contest_name'] in created_names:
                # Contest exists
                created = created_names[planned['contest_name']]
                status_data['created_contests'].append({
                    'name': planned['contest_name'],
                    'round': round_num,
                    'type': planned['contest_type'],
                    'domjudge_id': created['domjudge_contest_id'],
                    'status': 'created'
                })
                status_data['by_round'][round_num]['created'] += 1
            else:
                # Contest missing
                status_data['missing_contests'].append({
                    'name': planned['contest_name'],
                    'round': round_num,
                    'type': planned['contest_type'],
                    'status': 'missing'
                })
                status_data['by_round'][round_num]['missing'].append(planned['contest_name'])

        return status_data

    def verify_contest_setup(self) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Comprehensive verification of contest setup.
        Returns: (is_complete, errors, status_info)
        """
        errors = []

        # Check contest creation status
        status = self.get_contest_creation_status()

        if status['total_created'] == 0:
            errors.append("No contests have been created in DOMjudge")
        elif status['total_created'] < status['total_planned']:
            missing_count = len(status['missing_contests'])
            errors.append(f"{missing_count} contests are missing from DOMjudge")

        # Check DOMjudge database connection
        if not self.domjudge_db.connect():
            errors.append("Cannot connect to DOMjudge database")
        else:
            self.domjudge_db.disconnect()

        # Validate contest structure
        is_valid, structure_errors = self.contest_engine.validate_contest_structure()
        if not is_valid:
            errors.extend([f"Contest structure: {error}" for error in structure_errors])

        status_info = {
            'contests_status': status,
            'structure_valid': is_valid
        }

        is_complete = len(errors) == 0
        return is_complete, errors, status_info

    def delete_all_contests(self) -> Dict[str, Any]:
        """
        Delete all contests from both DOMjudge and local database.
        WARNING: This is a destructive operation!
        """
        print("🗑️ Deleting all contests...")

        results = {
            'local_deleted': 0,
            'domjudge_deleted': 0,
            'errors': []
        }

        try:
            # Delete from local database first
            delete_local_query = f"DELETE FROM {TABLE_NAMES['contests']}"
            if self.db_manager.execute_query(delete_local_query):
                results['local_deleted'] = self.db_manager.fetch_one("SELECT ROW_COUNT() as count")['count']
                print(f"  ✅ Deleted {results['local_deleted']} contests from local database")
            else:
                results['errors'].append("Failed to delete contests from local database")

            # Note: We don't delete from DOMjudge via API as it's more complex
            # and would require individual DELETE requests for each contest
            print("  ⚠️ DOMjudge contests not deleted (manual cleanup required)")

        except Exception as e:
            results['errors'].append(f"Delete operation failed: {e}")

        return results
