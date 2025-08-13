"""
Configuration settings for CoderCombat Tournament Management System
"""

import os
from dotenv import load_dotenv
# Load .env variables
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'tournament': {
        'host': os.getenv('TOURNAMENT_DB_HOST', 'localhost'),
        'port': int(os.getenv('TOURNAMENT_DB_PORT', 3306)),
        'user': os.getenv('TOURNAMENT_DB_USER', 'coder'),
        'password': os.getenv('TOURNAMENT_DB_PASSWORD', 'admin'),
        'database': os.getenv('TOURNAMENT_DB_NAME', 'codercombat'),
        'charset': os.getenv('TOURNAMENT_DB_CHARSET', 'utf8mb4')
    },
    'domjudge': {
        'host': os.getenv('DOMJUDGE_DB_HOST', 'localhost'),
        'port': int(os.getenv('DOMJUDGE_DB_PORT', 13306)),
        'user': os.getenv('DOMJUDGE_DB_USER', 'root'),
        'password': os.getenv('DOMJUDGE_DB_PASSWORD', 'root'),
        'database': os.getenv('DOMJUDGE_DB_NAME', 'domjudge'),
        'charset': os.getenv('DOMJUDGE_DB_CHARSET', 'utf8mb4')
    }
}

# DOMjudge API Configuration
DOMJUDGE_API_CONFIG = {
    'base_url': os.getenv('DOMJUDGE_API_BASE_URL', 'http://localhost:12345/api/v4'),
    'username': os.getenv('DOMJUDGE_API_USERNAME', 'admin'),
    'password': os.getenv('DOMJUDGE_API_PASSWORD', 'password'),
    'timeout': int(os.getenv('DOMJUDGE_API_TIMEOUT', 30))
}

# Tournament Configuration
TOURNAMENT_CONFIG = {
    'total_teams': int(os.getenv('TOURNAMENT_TOTAL_TEAMS', 48)),
    'total_rounds': int(os.getenv('TOURNAMENT_TOTAL_ROUNDS', 8)),
    'contest_duration_minutes': int(os.getenv('TOURNAMENT_CONTEST_DURATION', 50)),
    'wrong_submission_penalty_minutes': int(os.getenv('TOURNAMENT_PENALTY', 5)),
    'default_activation_delay_hours': int(os.getenv('TOURNAMENT_DEFAULT_DELAY', 48))
}

# Contest Configuration by Round (static)
ROUND_CONFIG = {
    1: {'contests': {'duels': 24}, 'problems': {'duel': 3}},
    2: {'contests': {'duels_winners': 12, 'groups_losers': 1}, 'problems': {'duel': 3, 'group': 4}},
    3: {'contests': {'duels_winners': 8, 'groups_losers': 1}, 'problems': {'duel': 3, 'group': 4}},
    4: {'contests': {'duels_winners': 4, 'groups_losers': 1, 'speed_eliminated': 1}, 'problems': {'duel': 3, 'group': 4, 'speed': 5}},
    5: {'contests': {'groups_losers': 1, 'speed_eliminated': 1}, 'problems': {'group': 4, 'speed': 5}},
    6: {'contests': {'duels': 4}, 'problems': {'duel': 3}},
    7: {'contests': {'duels_winners': 2, 'groups_losers': 1}, 'problems': {'duel': 3, 'group': 4}},
    8: {'contests': {'final': 1, 'third_place': 1}, 'problems': {'duel': 3}}
}

# Contest Naming Templates (static)
CONTEST_NAMING = {
    'duel': 'R{round}_Duel_{number:02d}',
    'group': 'R{round}_Group_{league}',
    'speed': 'R{round}_Speed_{type}',
    'final': 'R{round}_Final',
    'third_place': 'R{round}_Third_Place'
}

# Menu Display Settings
MENU_CONFIG = {
    'header_width': int(os.getenv('MENU_HEADER_WIDTH', 60)),
    'separator_char': os.getenv('MENU_SEPARATOR_CHAR', '='),
    'show_state_info': os.getenv('MENU_SHOW_STATE_INFO', 'True').lower() == 'true',
    'clear_screen': os.getenv('MENU_CLEAR_SCREEN', 'False').lower() == 'true'
}

# System Messages (static)
MESSAGES = {
    'welcome': '🏆 CoderCombat Tournament Management System',
    'goodbye': '👋 Goodbye!',
    'db_connected': '✅ Connected to database',
    'db_failed': '❌ Database connection failed',
    'invalid_choice': '❌ Invalid choice. Please try again.',
    'operation_success': '✅ Operation completed successfully',
    'operation_failed': '❌ Operation failed',
    'not_implemented': '🚧 Feature coming soon!'
}

# Database Table Names (static)
TABLE_NAMES = {
    'teams': 'teams',
    'contests': 'contests',
    'team_contests': 'team_contests',
    'tournament_state': 'tournament_state'
}

# Tournament States (static)
TOURNAMENT_STATES = {
    'SETUP': 'setup',
    'ROUND_ACTIVE': 'round_active',
    'PROCESSING_RESULTS': 'processing_results',
    'READY_NEXT_ROUND': 'ready_next_round',
    'COMPLETED': 'completed'
}

# Contest Types (static)
CONTEST_TYPES = {
    'DUEL': 'duel',
    'GROUP': 'group',
    'SPEED': 'speed'
}

# Team Assignment Status (static)
ASSIGNMENT_STATUS = {
    'ASSIGNED': 'assigned',
    'COMPLETED': 'completed'
}
