"""
DOMjudge REST API Client
Handles API operations for contest management and data retrieval
"""

import requests
import json
from typing import Optional, Dict, Any, List
from config import DOMJUDGE_API_CONFIG, MESSAGES


class DOMjudgeAPI:
    """REST API client for DOMjudge v8.2 API v4"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DOMJUDGE_API_CONFIG
        self.base_url = self.config['base_url']
        self.auth = (self.config['username'], self.config['password'])
        self.timeout = self.config['timeout']
        self.session = requests.Session()
        self.session.auth = self.auth

    def _make_request(self, method: str, endpoint: str, data: Dict = None,
                      params: Dict = None) -> Optional[Dict]:
        """
        Make an HTTP request to DOMjudge API
        Returns response data or None on failure
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            headers = {'Content-Type': 'application/json'} if data else {}

            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            response.raise_for_status()

            # Handle empty responses (e.g., DELETE operations)
            if response.status_code == 204 or not response.content:
                return {'success': True}

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {method} {endpoint} - {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ API response parsing failed: {e}")
            return None

    def test_connection(self) -> bool:
        """Test API connection by fetching basic info"""
        result = self._make_request('GET', '/info')
        if result:
            print("✅ DOMjudge API connection successful")
            if 'api_version' in result:
                print(f"📊 API Version: {result['api_version']}")
            return True
        else:
            print("❌ DOMjudge API connection failed")
            return False

    def get_info(self) -> Optional[Dict]:
        """Get DOMjudge system information"""
        return self._make_request('GET', '/info')

    def get_contests(self) -> Optional[List[Dict]]:
        """Get all contests"""
        return self._make_request('GET', '/contests')

    def get_contest(self, contest_id: str) -> Optional[Dict]:
        """Get specific contest by ID"""
        return self._make_request('GET', f'/contests/{contest_id}')

    def create_contest(self, contest_data: Dict) -> Optional[Dict]:
        """
        Create a new contest
        contest_data should include: name, start_time, duration, etc.
        """
        return self._make_request('POST', '/contests', data=contest_data)

    def update_contest(self, contest_id: str, contest_data: Dict) -> Optional[Dict]:
        """Update an existing contest"""
        return self._make_request('PUT', f'/contests/{contest_id}', data=contest_data)

    def get_teams(self) -> Optional[List[Dict]]:
        """Get teams, optionally filtered by contest"""
        endpoint = 'teams'
        return self._make_request('GET', endpoint)

    def get_teams_by_contest(self, contest_id: str = None) -> Optional[List[Dict]]:
        """Get teams, optionally filtered by contest"""
        endpoint = f'/contests/{contest_id}/teams'
        return self._make_request('GET', endpoint)


    def get_team(self, team_id: str, contest_id: str = None) -> Optional[Dict]:
        """Get specific team by ID"""
        endpoint = f'/teams/{team_id}'
        params = {'contest': contest_id} if contest_id else None
        return self._make_request('GET', endpoint, params=params)

    def get_organizations(self) -> Optional[List[Dict]]:
        """Get all organizations"""
        return self._make_request('GET', '/organizations')

    def get_problems(self, contest_id: str) -> Optional[List[Dict]]:
        """Get problems for a specific contest"""
        return self._make_request('GET', f'/contests/{contest_id}/problems')

    def get_scoreboard(self, contest_id: str, public: bool = False) -> Optional[Dict]:
        """Get scoreboard for a contest"""
        endpoint = f'/contests/{contest_id}/scoreboard'
        params = {'public': 'true' if public else 'false'}
        return self._make_request('GET', endpoint, params=params)

    def get_submissions(self, contest_id: str, team_id: str = None) -> Optional[List[Dict]]:
        """Get submissions for a contest, optionally filtered by team"""
        endpoint = f'/contests/{contest_id}/submissions'
        params = {'team': team_id} if team_id else None
        return self._make_request('GET', endpoint, params=params)

    def get_judgements(self, contest_id: str) -> Optional[List[Dict]]:
        """Get judgements for a contest"""
        return self._make_request('GET', f'/contests/{contest_id}/judgements')

    def get_languages(self) -> Optional[List[Dict]]:
        """Get all programming languages"""
        return self._make_request('GET', '/languages')

# Contest Management Helpers
    def get_contest_by_name(self, contest_name: str) -> Optional[Dict]:
        """Find a contest by its name"""
        contests = self.get_contests()
        if contests:
            for contest in contests:
                if contest.get('name') == contest_name:
                    return contest
        return None

    def is_contest_active(self, contest_id: str) -> Optional[bool]:
        """Check if a contest is currently active"""
        contest = self.get_contest(contest_id)
        if contest:
            # This would need to be implemented based on contest state logic
            # For now, return None to indicate unknown
            return None
        return None

    def get_contest_results(self, contest_id: str) -> Optional[Dict]:
        """
        Get comprehensive results for a contest
        Returns scoreboard with additional processing info
        """
        scoreboard = self.get_scoreboard(contest_id)
        if scoreboard:
            # Add additional result processing here if needed
            return {
                'contest_id': contest_id,
                'scoreboard': scoreboard,
                'processed_at': None  # Add timestamp when we process this
            }
        return None

    # Batch Operations
    def get_multiple_contests(self, contest_ids: List[str]) -> Dict[str, Optional[Dict]]:
        """Get multiple contests by their IDs"""
        results = {}
        for contest_id in contest_ids:
            results[contest_id] = self.get_contest(contest_id)
        return results

    def verify_api_access(self) -> Dict[str, bool]:
        """Verify API access to different endpoints"""
        checks = {
            'connection': False,
            'contests': False,
            'teams': False,
            'info': False
        }

        print("🔍 Verifying DOMjudge API access...")

        # Test connection
        if self.test_connection():
            checks['connection'] = True

            # Test contests endpoint
            if self.get_contests() is not None:
                checks['contests'] = True
                print("✅ Contests endpoint accessible")

            # Test teams endpoint
            if self.get_teams() is not None:
                checks['teams'] = True
                print("✅ Teams endpoint accessible")

            # Test info endpoint
            if self.get_info() is not None:
                checks['info'] = True
                print("✅ Info endpoint accessible")

        return checks

    def close(self):
        """Close the API session"""
        if self.session:
            self.session.close()