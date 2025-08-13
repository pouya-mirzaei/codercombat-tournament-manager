"""
Database Manager for Tournament Database Operations
Handles all raw SQL operations for the tournament management system
"""

import pymysql
from typing import Optional, Dict, Any, List
from config import DB_CONFIG, MESSAGES, TABLE_NAMES, TOURNAMENT_STATES


class DatabaseManager:
    """Manages tournament database operations with raw SQL"""

    def __init__(self, db_config: Dict[str, Any] = None):
        self.config = db_config or DB_CONFIG['tournament']
        self.connection: Optional[pymysql.Connection] = None

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(**self.config)
            print(f"{MESSAGES['db_connected']}: {self.config['database']}")
            return True
        except pymysql.Error as e:
            print(f"{MESSAGES['db_failed']}: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.connection is not None

    def execute_query(self, query: str, params: tuple = ()) -> bool:
        """Execute a query (INSERT, UPDATE, DELETE)"""
        if not self.connection:
            print(f"{MESSAGES['db_failed']}: No connection")
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return True
        except pymysql.Error as e:
            print(f"{MESSAGES['operation_failed']}: {e}")
            self.connection.rollback()
            return False

    def fetch_query(self, query: str, params: tuple = ()) -> Optional[List[Dict]]:
        """Execute a SELECT query and return results"""
        if not self.connection:
            print(f"{MESSAGES['db_failed']}: No connection")
            return None

        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except pymysql.Error as e:
            print(f"{MESSAGES['operation_failed']}: {e}")
            return None

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Execute a SELECT query and return first result"""
        results = self.fetch_query(query, params)
        return results[0] if results else None

    def initialize_database(self) -> bool:
        """Create all tournament tables"""
        print("🔧 Creating tournament database tables...")

        # Teams table - stores team information and DOMjudge mappings
        teams_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAMES['teams']} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            domjudge_team_id INT NULL,
            domjudge_user_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_domjudge_team_id (domjudge_team_id),
            INDEX idx_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        # Contests table - stores contest definitions and DOMjudge mappings
        contests_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAMES['contests']} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            contest_name VARCHAR(100) NOT NULL UNIQUE,
            round_number INT NOT NULL,
            contest_type ENUM('duel', 'group', 'speed') NOT NULL,
            domjudge_contest_id INT NULL,
            max_teams INT NOT NULL,
            problems_count INT NOT NULL DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_round_type (round_number, contest_type),
            INDEX idx_domjudge_contest_id (domjudge_contest_id),
            INDEX idx_contest_name (contest_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        # Team contest assignments - tracks which teams are in which contests
        team_contests_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAMES['team_contests']} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            team_id INT NOT NULL,
            contest_id INT NOT NULL,
            result_rank INT NULL,
            problems_solved INT NULL,
            total_time_seconds INT NULL,
            penalty_time_seconds INT NULL DEFAULT 0,
            status ENUM('assigned', 'completed') DEFAULT 'assigned',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES {TABLE_NAMES['teams']}(id) ON DELETE CASCADE,
            FOREIGN KEY (contest_id) REFERENCES {TABLE_NAMES['contests']}(id) ON DELETE CASCADE,
            UNIQUE KEY unique_team_contest (team_id, contest_id),
            INDEX idx_contest_status (contest_id, status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        # Tournament state tracking - maintains current tournament status
        tournament_state_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAMES['tournament_state']} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            current_round INT NOT NULL DEFAULT 1,
            current_phase ENUM('setup', 'round_active', 'processing_results', 'ready_next_round', 'completed') DEFAULT 'setup',
            total_teams INT NOT NULL DEFAULT 48,
            winners_league_count INT NOT NULL DEFAULT 0,
            losers_league_count INT NOT NULL DEFAULT 0,
            eliminated_count INT NOT NULL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            notes TEXT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        # Execute table creation
        tables = [
            ("teams", teams_table),
            ("contests", contests_table),
            ("team_contests", team_contests_table),
            ("tournament_state", tournament_state_table)
        ]

        success_count = 0
        for table_name, query in tables:
            if self.execute_query(query):
                print(f"✅ Table '{table_name}' created successfully")
                success_count += 1
            else:
                print(f"❌ Failed to create table '{table_name}'")

        # Initialize tournament state if not exists
        init_state_query = f"""
        INSERT IGNORE INTO {TABLE_NAMES['tournament_state']} 
        (id, current_round, current_phase, total_teams) 
        VALUES (1, 1, %s, 48)
        """

        if self.execute_query(init_state_query, (TOURNAMENT_STATES['SETUP'],)):
            print("✅ Tournament state initialized")
            success_count += 1

        return success_count == len(tables) + 1

    def get_tournament_state(self) -> Optional[Dict]:
        """Get current tournament state"""
        query = f"SELECT * FROM {TABLE_NAMES['tournament_state']} WHERE id = 1"
        return self.fetch_one(query)

    def update_tournament_state(self, **kwargs) -> bool:
        """Update tournament state with provided fields"""
        if not kwargs:
            return False

        # Build dynamic UPDATE query
        set_clauses = []
        params = []

        for field, value in kwargs.items():
            set_clauses.append(f"{field} = %s")
            params.append(value)

        query = f"""
        UPDATE {TABLE_NAMES['tournament_state']} 
        SET {', '.join(set_clauses)}
        WHERE id = 1
        """

        return self.execute_query(query, tuple(params))

    def get_teams_count(self) -> int:
        """Get total number of teams"""
        query = f"SELECT COUNT(*) as count FROM {TABLE_NAMES['teams']}"
        result = self.fetch_one(query)
        return result['count'] if result else 0

    def get_contests_by_round(self, round_number: int) -> List[Dict]:
        """Get all contests for a specific round"""
        query = f"""
        SELECT * FROM {TABLE_NAMES['contests']} 
        WHERE round_number = %s 
        ORDER BY contest_type, contest_name
        """
        return self.fetch_query(query, (round_number,)) or []

    def test_connection(self) -> bool:
        """Test database connection with a simple query"""
        if not self.connection:
            return False

        try:
            query = "SELECT 1 as test"
            result = self.fetch_one(query)
            return result is not None and result.get('test') == 1
        except:
            return False