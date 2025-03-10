# default data for custom json-stored items
def get_default_puzzle_bingo_game_data():
    return {
        "bingo_coin_num": 10, 
        "known_rules": {},  # Dict[int, str]
        "bingo_spoiled": '',  # Literal['', SPOIL_TEXT]
        "word_history": [],  # List[str]
    }

def get_default_puzzle_genshin_game_data():
    return {
        "placeholder": 1,  # TODO
    }