import re


class Statistics:
    """A class that stores data for statistics calculations of the players' performance"""
    def __init__(self):
        self.player_stats = {}  # Dictionary to store player statistics
        self.player_victories = {}  # Dictionary to store player victories
        self.player_games_played = {}  # Dictionary to store number of games each player played

    def extract_round_number(self,message):
        round_number_match = re.search(r'Round (\d+)', message)
        if round_number_match:
            round_number = int(round_number_match.group(1))
            return round_number
        else:
            return None
            
