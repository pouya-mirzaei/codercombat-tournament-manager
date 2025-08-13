"""
Configuration package for CoderCombat Tournament Management System
"""

from .settings import (
    DB_CONFIG,
    DOMJUDGE_API_CONFIG,
    TOURNAMENT_CONFIG,
    ROUND_CONFIG,
    CONTEST_NAMING,
    MENU_CONFIG,
    MESSAGES,
    TABLE_NAMES,
    TOURNAMENT_STATES,
    CONTEST_TYPES,
    ASSIGNMENT_STATUS
)

__all__ = [
    'DB_CONFIG',
    'DOMJUDGE_API_CONFIG',
    'TOURNAMENT_CONFIG',
    'ROUND_CONFIG',
    'CONTEST_NAMING',
    'MENU_CONFIG',
    'MESSAGES',
    'TABLE_NAMES',
    'TOURNAMENT_STATES',
    'CONTEST_TYPES',
    'ASSIGNMENT_STATUS'
]