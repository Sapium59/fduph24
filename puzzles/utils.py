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
