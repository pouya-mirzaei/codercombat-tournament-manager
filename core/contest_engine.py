"""
Contest Engine - Sub-Step 3.1: Contest Data Structure & Validation
Handles contest generation, naming, and team flow mapping based on tournament rules
"""

from typing import Dict, List, Tuple, Optional, Any
from config import ROUND_CONFIG, CONTEST_NAMING, TOURNAMENT_CONFIG


class ContestEngine:
    """Manages contest structure, generation, and team flow mapping"""

    def __init__(self):
        # Contest flow mapping based on your tournament diagram
        self.CONTEST_FLOW = self._initialize_contest_flow_mapping()

    def _initialize_contest_flow_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the complete contest flow mapping based on tournament diagram"""
        return {
            # Round 1 - 24 Duels (Winners to R2 duels, Losers to R2 group)
            **{f"R1_Duel_{i:02d}": {
                "winner_to": f"R2_Duel_{((i - 1) // 2) + 1:02d}",  # 2 R1 winners per R2 duel
                "loser_to": "R2_Group_Losers"
            } for i in range(1, 25)},

            # Round 2 - 12 Duels + 1 Group
            **{f"R2_Duel_{i:02d}": {
                "winner_to": f"R3_Duel_{((i - 1) // 2) + 1:02d}" if i <= 8 else f"R3_Duel_{i - 4:02d}",
                "loser_to": "R3_Group_Losers"
            } for i in range(1, 13)},

            "R2_Group_Losers": {
                "rank_1_to": "R3_Duel_05",  # Best from losers group
                "rank_2_to": "R3_Duel_06",
                "rank_3_to": "R3_Duel_07",
                "rank_4_to": "R3_Duel_08",
                "rank_5_plus_to": "R3_Group_Losers"  # Rest go to R3 losers group
            },

            # Round 3 - 8 Duels + 1 Group
            **{f"R3_Duel_{i:02d}": {
                "winner_to": f"R4_Duel_{((i - 1) // 2) + 1:02d}",
                "loser_to": "R4_Group_Losers"
            } for i in range(1, 9)},

            "R3_Group_Losers": {
                "eliminated": True,  # Teams ranked 25-48
                "final_ranks": list(range(25, 49))
            },

            # Round 4 - 4 Duels + 1 Group + 1 Speed
            **{f"R4_Duel_{i:02d}": {
                "winner_to": "R5_Rest",  # Winners rest in R5
                "loser_to": "R5_Group_Losers"
            } for i in range(1, 5)},

            "R4_Group_Losers": {
                "all_to": "R5_Group_Losers"  # All continue to R5 group
            },

            "R4_Speed_Eliminated": {
                "ranking_only": True,  # Just for ranking eliminated teams
                "final_ranks": list(range(25, 49))
            },

            # Round 5 - 1 Group + 1 Speed (Winners rest)
            "R5_Group_Losers": {
                "rank_1_to": "R6_Duel_01",
                "rank_2_to": "R6_Duel_02",
                "rank_3_to": "R6_Duel_03",
                "rank_4_to": "R6_Duel_04",
                "rank_5_plus_to": "eliminated",
                "final_ranks": list(range(9, 25))  # Teams ranked 9-24
            },

            "R5_Speed_Eliminated": {
                "ranking_only": True,  # Final ranking for eliminated teams
                "final_ranks": list(range(25, 49))
            },

            # Round 6 - 4 Duels (Promoted losers vs Rested winners)
            **{f"R6_Duel_{i:02d}": {
                "winner_to": f"R7_Duel_{((i - 1) // 2) + 1:02d}",
                "loser_to": "R7_Group_Losers"
            } for i in range(1, 5)},

            # Round 7 - 2 Semi-finals + 1 Group
            "R7_Duel_01": {  # Semi-final 1
                "winner_to": "R8_Final",
                "loser_to": "R8_Third_Place"
            },

            "R7_Duel_02": {  # Semi-final 2
                "winner_to": "R8_Final",
                "loser_to": "R8_Third_Place"
            },

            "R7_Group_Losers": {
                "final_ranks": list(range(5, 9))  # Teams ranked 5-8
            },

            # Round 8 - Final + Third Place
            "R8_Final": {
                "winner_rank": 1,
                "loser_rank": 2
            },

            "R8_Third_Place": {
                "winner_rank": 3,
                "loser_rank": 4
            }
        }

    def generate_all_contests(self) -> List[Dict[str, Any]]:
        """Generate all contests for all rounds based on ROUND_CONFIG"""
        all_contests = []

        for round_num in range(1, TOURNAMENT_CONFIG['total_rounds'] + 1):
            round_contests = self.generate_round_contests(round_num)
            all_contests.extend(round_contests)

        return all_contests

    def generate_round_contests(self, round_number: int) -> List[Dict[str, Any]]:
        """Generate contests for a specific round"""
        if round_number not in ROUND_CONFIG:
            raise ValueError(f"Invalid round number: {round_number}")

        round_config = ROUND_CONFIG[round_number]
        contests = []

        # Generate each contest type for the round
        for contest_type, count in round_config['contests'].items():
            contest_list = self._generate_contests_by_type(
                round_number, contest_type, count, round_config['problems']
            )
            contests.extend(contest_list)

        return contests

    def _generate_contests_by_type(self, round_num: int, contest_type: str, count: int,
                                   problems_config: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate contests of a specific type"""
        contests = []

        if contest_type == 'duels':
            # Regular duels
            for i in range(1, count + 1):
                contest_name = CONTEST_NAMING['duel'].format(round=round_num, number=i)
                contests.append(self._create_contest_data(
                    contest_name, round_num, 'duel', 2, problems_config['duel']
                ))

        elif contest_type == 'duels_winners':
            # Winner duels (same as regular duels but different semantics)
            for i in range(1, count + 1):
                contest_name = CONTEST_NAMING['duel'].format(round=round_num, number=i)
                contests.append(self._create_contest_data(
                    contest_name, round_num, 'duel', 2, problems_config['duel']
                ))

        elif contest_type == 'groups_losers':
            # Losers group contest
            contest_name = CONTEST_NAMING['group'].format(round=round_num, league='Losers')
            # Calculate max teams based on round
            max_teams = self._calculate_group_max_teams(round_num, 'losers')
            contests.append(self._create_contest_data(
                contest_name, round_num, 'group', max_teams, problems_config['group']
            ))

        elif contest_type == 'speed_eliminated':
            # Speed contest for eliminated teams
            contest_name = CONTEST_NAMING['speed'].format(round=round_num, type='Eliminated')
            max_teams = self._calculate_speed_max_teams(round_num)
            contests.append(self._create_contest_data(
                contest_name, round_num, 'speed', max_teams, problems_config['speed']
            ))

        elif contest_type == 'final':
            # Final contest
            contest_name = CONTEST_NAMING['final'].format(round=round_num)
            contests.append(self._create_contest_data(
                contest_name, round_num, 'duel', 2, problems_config['duel']
            ))

        elif contest_type == 'third_place':
            # Third place contest
            contest_name = CONTEST_NAMING['third_place'].format(round=round_num)
            contests.append(self._create_contest_data(
                contest_name, round_num, 'duel', 2, problems_config['duel']
            ))

        return contests

    def _create_contest_data(self, name: str, round_num: int, contest_type: str,
                             max_teams: int, problems_count: int) -> Dict[str, Any]:
        """Create a contest data dictionary"""
        return {
            'contest_name': name,
            'round_number': round_num,
            'contest_type': contest_type,
            'max_teams': max_teams,
            'problems_count': problems_count,
            'duration_minutes': TOURNAMENT_CONFIG['contest_duration_minutes'],
            'penalty_minutes': TOURNAMENT_CONFIG['wrong_submission_penalty_minutes'],
            'domjudge_contest_id': None,  # Will be set when created in DOMjudge
            'status': 'planned'  # planned -> created -> activated -> started -> finished
        }

    def _calculate_group_max_teams(self, round_num: int, league: str) -> int:
        """Calculate maximum teams for group contests"""
        if round_num == 2 and league == 'losers':
            return 24  # All R1 losers
        elif round_num == 3 and league == 'losers':
            return 32  # R2 group overflow + R2 duel losers
        elif round_num == 4 and league == 'losers':
            return 16  # R3 duel losers
        elif round_num == 5 and league == 'losers':
            return 8  # R4 group + R4 duel losers
        elif round_num == 7 and league == 'losers':
            return 4  # R6 duel losers
        else:
            return 24  # Default fallback

    def _calculate_speed_max_teams(self, round_num: int) -> int:
        """Calculate maximum teams for speed contests"""
        if round_num == 4:
            return 24  # Eliminated teams from R3
        elif round_num == 5:
            return 36
        else:
            return 24  # Default fallback

    def get_contest_flow(self, contest_name: str) -> Optional[Dict[str, Any]]:
        """Get the flow mapping for a specific contest"""
        return self.CONTEST_FLOW.get(contest_name)

    def validate_contest_structure(self) -> Tuple[bool, List[str]]:
        """Validate the complete contest structure for consistency"""
        errors = []

        # Check total contest counts
        total_contests = 0
        for round_num, config in ROUND_CONFIG.items():
            round_total = sum(config['contests'].values())
            total_contests += round_total

        # Validate flow mapping completeness
        all_contests = self.generate_all_contests()
        for contest in all_contests:
            contest_name = contest['contest_name']
            if contest_name not in self.CONTEST_FLOW:
                errors.append(f"Missing flow mapping for contest: {contest_name}")

        # Validate team count consistency
        if not self._validate_team_flow():
            errors.append("Team flow validation failed - teams don't add up correctly")

        return len(errors) == 0, errors

    def _validate_team_flow(self) -> bool:
        """Validate that team counts flow correctly through rounds"""
        # This would implement complex validation logic
        # For now, basic validation that we start with 48 teams
        return TOURNAMENT_CONFIG['total_teams'] == 48

    def get_contest_summary(self) -> Dict[str, Any]:
        """Get a summary of all contests in the tournament"""
        all_contests = self.generate_all_contests()

        summary = {
            'total_contests': len(all_contests),
            'by_round': {},
            'by_type': {'duel': 0, 'group': 0, 'speed': 0}
        }

        for contest in all_contests:
            round_num = contest['round_number']
            contest_type = contest['contest_type']

            # Count by round
            if round_num not in summary['by_round']:
                summary['by_round'][round_num] = 0
            summary['by_round'][round_num] += 1

            # Count by type
            summary['by_type'][contest_type] += 1

        return summary

    def get_initial_team_placement(self) -> Dict[str, List[int]]:
        """
        Generate initial team placement for Round 1
        Returns dict mapping contest names to team IDs (1-48)
        This will be used when teams are actually placed in contests
        """
        placement = {}
        team_id = 1

        # Place 2 teams in each of the 24 R1 duels
        for i in range(1, 25):
            contest_name = f"R1_Duel_{i:02d}"
            placement[contest_name] = [team_id, team_id + 1]
            team_id += 2

        return placement
