"""
Core package for CoderCombat Tournament Management System
Contains database managers and core business logic
"""

from .database import DatabaseManager
from .contest_engine import ContestEngine
from .contest_manager import ContestManager

__all__ = [
    'DatabaseManager',
    'ContestEngine',
    'ContestManager',
]
