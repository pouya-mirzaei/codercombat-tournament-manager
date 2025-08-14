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

    def create_user(self, username: str, name: str, email: str, password: str, role: str = 'team') -> Optional[int]:
        """
        Create a new user in DOMjudge database
        Returns the created user ID on success, None on failure
        """
        if self.user_exists(username):
            print(f"❌ User '{username}' already exists in DOMjudge")
            return None

        # Get next available user ID
        user_id = self.get_next_user_id()
        if user_id is None:
            print("❌ Could not determine next user ID")
            return None

        # Hash password using DOMjudge's method (MD5 - legacy but what DOMjudge uses)
        password_hash = hashlib.md5(password.encode()).hexdigest()

        # Insert user record
        user_query = """
        INSERT INTO user (userid, username, name, email, password, enabled, teamid)
        VALUES (%s, %s, %s, %s, %s, 1, NULL)
        """

        if self.execute_query(user_query, (user_id, username, name, email, password_hash)):
            # Add user role
            role_query = "INSERT INTO userrole (userid, roleid) VALUES (%s, %s)"
            role_id = 3 if role == 'team' else 1  # 3 = team role, 1 = admin role

            if self.execute_query(role_query, (user_id, role_id)):
                print(f"✅ Created user: {username} (ID: {user_id})")
                return user_id
            else:
                print(f"❌ Failed to assign role to user: {username}")
                return None
        else:
            print(f"❌ Failed to create user: {username}")
            return None

    def create_team(self, team_name: str, category_id: int = 1) -> Optional[int]:
        """
        Create a new team in DOMjudge database
        Returns the created team ID on success, None on failure
        """
        if self.team_exists(team_name):
            print(f"❌ Team '{team_name}' already exists in DOMjudge")
            return None

        # Get next available team ID
        team_id = self.get_next_team_id()
        if team_id is None:
            print("❌ Could not determine next team ID")
            return None

        # Insert team record
        team_query = """
        INSERT INTO team (teamid, name, categoryid, enabled, visible)
        VALUES (%s, %s, %s, 1, 1)
        """

        if self.execute_query(team_query, (team_id, team_name, category_id)):
            print(f"✅ Created team: {team_name} (ID: {team_id})")
            return team_id
        else:
            print(f"❌ Failed to create team: {team_name}")
            return None

    def link_user_to_team(self, user_id: int, team_id: int) -> bool:
        """Link a user to a team in DOMjudge"""
        query = "UPDATE user SET teamid = %s WHERE userid = %s"

        if self.execute_query(query, (team_id, user_id)):
            print(f"✅ Linked user {user_id} to team {team_id}")
            return True
        else:
            print(f"❌ Failed to link user {user_id} to team {team_id}")
            return False

    def create_team_with_user(self, team_name: str, username: str, email: str,
                              password: str, category_id: int = 1) -> Optional[Dict[str, int]]:
        """
        Create both team and user, then link them together
        Returns dict with 'user_id' and 'team_id' on success, None on failure
        """
        print(f"🔨 Creating team '{team_name}' with user '{username}'...")

        # Create team first
        team_id = self.create_team(team_name, category_id)
        if team_id is None:
            return None

        # Create user
        user_id = self.create_user(username, team_name, email, password, 'team')
        if user_id is None:
            print(f"❌ Team created but user creation failed. Team ID: {team_id}")
            return None

        # Link user to team
        if self.link_user_to_team(user_id, team_id):
            print(f"🎉 Successfully created team '{team_name}' (Team ID: {team_id}, User ID: {user_id})")
            return {'user_id': user_id, 'team_id': team_id}
        else:
            print(f"❌ Team and user created but linking failed")
            return None

    def get_all_teams(self) -> List[Dict]:
        """Get all teams from DOMjudge database"""
        query = """
        SELECT t.teamid, t.name, t.categoryid, t.enabled, t.visible,
               u.userid, u.username, u.email
        FROM team t
        LEFT JOIN user u ON u.teamid = t.teamid
        ORDER BY t.teamid
        """
        return self.fetch_query(query) or []

    def get_team_categories(self) -> List[Dict]:
        """Get all team categories from DOMjudge"""
        query = "SELECT categoryid, name, color FROM team_category ORDER BY categoryid"
        return self.fetch_query(query) or []

    def verify_domjudge_schema(self) -> bool:
        """Verify that DOMjudge database has expected tables and structure"""
        required_tables = ['user', 'team', 'team_category', 'userrole', 'role']

        print("🔍 Verifying DOMjudge database schema...")

        for table in required_tables:
            query = f"SHOW TABLES LIKE '{table}'"
            result = self.fetch_query(query)

            if not result:
                print(f"❌ Required table '{table}' not found")
                return False
            else:
                print(f"✅ Table '{table}' found")

        print("✅ DOMjudge schema verification complete")
        return True

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