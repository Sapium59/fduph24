# default data for custom json-stored items
def get_default_puzzle_bingo_game_data():
    return {
        "bingo_coin_num": 10, 
        "known_rules": {
            25: '无重复字母',
            26: '恰在一条线上差一点BINGO', 
        },  # Dict[int, str]
        "bingo_spoiled": '',  # Literal['', SPOIL_TEXT]
        "word_history": [],  # List[str]
    }

def get_default_puzzle_genshin_game_data():
    return {
        "history": []
    }

from datetime import timedelta
from django.utils import timezone
def count_6am_6pm_between(start_time, end_time):
    # Calculate the number of days between the start and end times
    num_days = (end_time - start_time).days

    # Calculate the number of occurrences of 6 am and 6 pm
    count_6am = num_days * 2  # Two occurrences per day (6 am and 6 pm)
    count_6pm = num_days * 2

    # Adjust the counts based on the actual hours of the start and end times
    if start_time.hour > 8:
        count_6am -= 1
    if end_time.hour < 20:
        count_6pm -= 1

    return count_6am, count_6pm