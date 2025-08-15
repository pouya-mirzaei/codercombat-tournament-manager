"""
DOMjudge Database Manager
Direct database operations on DOMjudge database for user and team management
"""

import pymysql
import hashlib
from typing import Optional, Dict, Any, List
from config import DB_CONFIG, MESSAGES


class DOMjudgeDBManager:
    """Manages direct database operations on DOMjudge database"""

    def __init__(self, db_config: Dict[str, Any] = None):
        self.config = db_config or DB_CONFIG['domjudge']
        self.connection: Optional[pymysql.Connection] = None

    def connect(self) -> bool:
        """Establish connection to DOMjudge database"""
        try:
            self.connection = pymysql.connect(**self.config)
            print(f"{MESSAGES['db_connected']}: DOMjudge DB ({self.config['database']})")
            return True
        except pymysql.Error as e:
            print(f"{MESSAGES['db_failed']}: DOMjudge DB - {e}")
            return False

    def disconnect(self):
        """Close DOMjudge database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        """Check if DOMjudge database is connected"""
        return self.connection is not None

    def execute_query(self, query: str, params: tuple = ()) -> bool:
        """Execute a query (INSERT, UPDATE, DELETE) on DOMjudge DB"""
        if not self.connection:
            print(f"{MESSAGES['db_failed']}: DOMjudge DB - No connection")
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return True
        except pymysql.Error as e:
            print(f"{MESSAGES['operation_failed']}: DOMjudge DB - {e}")
            self.connection.rollback()
            return False

    def fetch_query(self, query: str, params: tuple = ()) -> Optional[List[Dict]]:
        """Execute a SELECT query on DOMjudge DB and return results"""
        if not self.connection:
            print(f"{MESSAGES['db_failed']}: DOMjudge DB - No connection")
            return None

        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except pymysql.Error as e:
            print(f"{MESSAGES['operation_failed']}: DOMjudge DB - {e}")
            return None

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Execute a SELECT query on DOMjudge DB and return first result"""
        results = self.fetch_query(query, params)
        return results[0] if results else None

    def get_next_user_id(self) -> Optional[int]:
        """Get the next available user ID for DOMjudge"""
        query = "SELECT COALESCE(MAX(userid), 0) + 1 as next_id FROM user"
        result = self.fetch_one(query)
        return result['next_id'] if result else None

    def get_next_team_id(self) -> Optional[int]:
        """Get the next available team ID for DOMjudge"""
        query = "SELECT COALESCE(MAX(teamid), 0) + 1 as next_id FROM team"
        result = self.fetch_one(query)
        return result['next_id'] if result else None

    def user_exists(self, username: str) -> bool:
        """Check if a user already exists in DOMjudge"""
        query = "SELECT COUNT(*) as count FROM user WHERE username = %s"
        result = self.fetch_one(query, (username,))
        return result['count'] > 0 if result else False

    def team_exists(self, team_name: str) -> bool:
        """Check if a team already exists in DOMjudge"""
        query = "SELECT COUNT(*) as count FROM team WHERE name = %s"
        result = self.fetch_one(query, (team_name,))
        return result['count'] > 0 if result else False

    def get_team_by_name(self, team_name: str) -> Optional[Dict]:
        """Get team information by team name"""
        query = "SELECT teamid, name, categoryid, enabled FROM team WHERE name = %s"
        return self.fetch_one(query, (team_name,))

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user information by username"""
        query = "SELECT userid, username, name, email, enabled FROM user WHERE username = %s"
        return self.fetch_one(query, (username,))


    def test_connection(self) -> bool:
        """Test DOMjudge database connection with a simple query"""
        if not self.connection:
            return False

        try:
            query = "SELECT COUNT(*) as count FROM team"
            result = self.fetch_one(query)
            return result is not None
        except:
            return False