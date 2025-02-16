import re
import traceback
import json
from typing import Tuple, Dict, List, Callable
from collections import OrderedDict

from django.views.decorators.http import require_POST

from puzzles.messaging import log_puzzle_info
from ..models import Team
from .r2q8_data import IPA_DICT, CHEMICAL_ELEMENTS, VOWELS


# constants
WORD_SET = set()
ADJ_SET = set()
ANIMAL_SET = set()
COUNTRY_SET = set()
DEFAULT_PUZZLE_BINGO_GAME_DATA = {
    "bingo_coin_num": 10, 
    "known_rules": [],  # List[int]
    "bingo_spoiled": False,
    "word_history": [],  # List[str]
}


# utils
def clear_word(word: str):
    cleared_word = "".join(re.findall("[A-Z]", word.upper()))
    return cleared_word


# rules
def count(string: str, char: str) -> int:
    return string.count(char)

def has_duplicate_letters(word: str) -> bool:
    letter_set = set()
    for char in word:
        if char in letter_set:
            return True
        letter_set.add(char)
    return False

def can_form_word_by_removing_one_letter(word: str) -> bool:
    for i in range(len(word)):
        new_word = word[:i] + word[i + 1:]
        if new_word in WORD_SET:
            return True
    return False

def is_component_word(word: str) -> bool:
    if word == 'IRELAND':
        return False
    if len(word) < 4:
        return False
    for i in range(2, len(word) - 2):
        prefix = word[:i]
        suffix = word[i:]
        if prefix in WORD_SET and suffix in WORD_SET:
            return True
    return False

def contains_five_letter_word(word: str) -> bool:
    if len(word) < 6:
        return False
    for dict_word in WORD_SET:
        if len(dict_word) == 5 and dict_word in word:
            return True
    return False

def is_alternating_vowel_consonant(word: str) -> bool:
    
    for i in range(len(word) - 1):
        current_char = word[i]
        next_char = word[i + 1]
        is_current_vowel = current_char in VOWELS
        is_next_vowel = next_char in VOWELS
        if is_current_vowel == is_next_vowel:
            return False
    return True

def get_n_closed_region(word: str) -> int:
    closed_regions = {
        'A': 1, 'B': 2, 'D': 1, 'O': 1, 'P': 1, 'Q': 1, 'R': 1,
    }
    total_regions = 0
    for char in word:
        total_regions += closed_regions.get(char, 0)
    return total_regions

def is_country_name(word: str) -> bool:
    for country in COUNTRY_SET:
        if country.replace(' ', '').replace('-', '').upper() == word:
            return True
    return False

def get_match_deg(word: str, line: str) -> int:
    return sum(1 for letter in word if letter in line.upper())

def get_remain_letter(word: str, line: str) -> str:
    for letter in line.upper():
        if letter not in word:
            return letter
    return None

def has_almost_line(word: str) -> bool:
    if has_duplicate_letters(word):
        return False
    lines = {
        'abcde', 'fghik', 'fghjk', 'lmnop', 'qrstu', 'vwxyz',
        'aflqv', 'bgmrw', 'chnsx', 'dioty', 'djoty', 'ekpuz',
        'agntz', 'einrv', 'ejnrv'
    }
    n_almost_line = 0
    for line in lines:
        if get_match_deg(word, line) == 4:
            remain_letter = get_remain_letter(word, line)
            if remain_letter == 'J':
                continue
            if remain_letter == 'I' and get_match_deg(word, 'djoty') != 4 and get_match_deg(word, 'ejnrv') != 4:
                continue
            n_almost_line += 1

    return n_almost_line == 1

RULES_LIST: List[Tuple[int, str, Callable[[str], bool]]] = [
    (0,  '含有音标/ɪ/', lambda word: bool(word in IPA_DICT and 'ɪ' in IPA_DICT[word])),
    (1,  '化学元素',    lambda word: bool(word.capitalize() in CHEMICAL_ELEMENTS)),
    (2,  '偶数长度',    lambda word: bool(len(word) % 2 == 0)),
    (3,  '含有E和L',    lambda word: bool('E' in word and 'L' in word)),
    (4,  '长度为6',     lambda word: bool(len(word) == 6)),
    (5,  'ED结尾',     lambda word: bool(word.endswith('ED'))),
    (6,  '含有L',       lambda word: bool('L' in word)),
    (7,  '哑音B',      lambda word: bool(word in IPA_DICT and count(IPA_DICT[word], 'b') < count(word.replace(r'(.)\1+', r'\1'), 'B'))),
    (8,  '含有I',      lambda word: bool('I' in word)),
    (9,  '去1字母成词', lambda word: can_form_word_by_removing_one_letter(word)),
    (10, '含有Y',      lambda word: bool('Y' in word)),
    (11, '含有M',      lambda word: bool('M' in word)),
    (12, '形容词',     lambda word: bool(word in ADJ_SET)),
    (13, '合成词',     lambda word: is_component_word(word)),
    (14, '含有5字母词', lambda word: contains_five_letter_word(word)),
    (15, '元辅音相间', lambda word: is_alternating_vowel_consonant(word)),
    (16, '大写字母有2个封闭区域', lambda word: get_n_closed_region(word) == 2),
    (17, '含有N',      lambda word: bool('N' in word)),
    (18, '辅音比元音多1个', lambda word: len([char for char in word if char not in VOWELS]) - len([char for char in word if char in VOWELS]) == 1),
    (19, '动物',       lambda word: bool(word in ANIMAL_SET)),
    (20, '含有T',      lambda word: bool('T' in word)),
    (21, '3个元音',    lambda word: len([char for char in word if char in VOWELS]) == 3),
    (22, '长度7或8',   lambda word: bool(len(word) in (7, 8))),
    (23, '国家',       lambda word: is_country_name(word)),
    (24, '含有A和E',   lambda word: bool('A' in word and 'E' in word)),
    (25, '无重复字母',  lambda word: not has_duplicate_letters(word)),
    (26, '恰在一条线上差一点BINGO', lambda word: has_almost_line(word)),
]


# key operations
def _get_newly_known_indice(triggered_rules_indice: List[int]) -> List[int]:
    LINES = [{i + 5 * j for i in range(5)} for j in range(5)] + \
        [{j + 5 * i for i in range(5)} for j in range(5)] + \
        [{0, 6, 12, 18, 24}]
    newly_known_lines = [line for line in LINES if all(index in triggered_rules_indice for index in line)]
    newly_known_indice = set([idx for line in newly_known_lines for idx in line])
    return sorted(list(newly_known_indice))

def update(puzzle_bingo_game_data, triggered_rules_indice):
    known_rules_indice: List[int] = puzzle_bingo_game_data["known_rules"]
    newly_known_indice: List[int] = _get_newly_known_indice(triggered_rules_indice)
    updated_known_rules_indice = sorted(list(set(known_rules_indice + newly_known_indice)))
    puzzle_bingo_game_data["known_rules"] = updated_known_rules_indice
    return puzzle_bingo_game_data


@require_POST
def submit(request):
    "A crude example of an interactive puzzle handler."
    # 2. Persist it on the server. You can just add a puzzle-specific model
    # with a foreign key to Team. If you have strong performance needs and are
    # feeling adventurous, you might even add an in-memory store like Redis or
    # something.
    #
    # Advantages of 2: Easy to share state between team members. Don't need
    # additional complexity to prevent client-side tampering with state. Easier
    # to collect statistics about solving after the fact. If you don't get
    # client-side state right the first time, fixing it after some solvers have
    # made partial progress can be a pain; server-side state lets you at least
    # keep the possibility of manually introspecting or fixing it as needed.

    try:
        # get user data
        puzzle_bingo_game_data = request.context.team.puzzle_bingo_game_data
        if not puzzle_bingo_game_data:
            puzzle_bingo_game_data = DEFAULT_PUZZLE_BINGO_GAME_DATA
        else:
            print(puzzle_bingo_game_data)
        bingo_coin_num = puzzle_bingo_game_data["bingo_coin_num"]
        bingo_spoiled = puzzle_bingo_game_data["bingo_spoiled"]

        # switch case guess_a_word / do_spoil / buy_a_sample
        body = json.loads(request.body)
        mode = body.get("mode")
        print(f"[I] r2q8: mode={mode}, body={body}")
        if mode == "guess_a_word":
            # submittion & rules check
            word = body.get("word", "")
            word = clear_word(word)
            triggered_rules_indice = [item[0] for item in RULES_LIST if item[2](word)]
            # TODO update user data
            request.context.team.puzzle_bingo_game_data = update(puzzle_bingo_game_data, triggered_rules_indice)
            request.context.team.save()
            ret_dict = {
                'error': '', 
                'correct': True,
                'triggered_rules': {idx: RULES_LIST[idx][1] for idx in triggered_rules_indice},
                bingo_coin_num: "bingo_coin_num",
                bingo_spoiled: "bingo_spoiled"
            }
        elif mode == "do_spoil":
            pass  # TODO
            ret_dict = {
                'error': '', 
                'correct': True,
            }
        elif mode == "buy_a_sample":
            pass  # TODO
            ret_dict = {}
        else:
            print(f"Warning: unknown mode in r2q8: {mode}")
            ret_dict = {}

        # when no error, ret_dict['error'] must be empty
        ret_dict['error'] = ''
        print(f"[I] r2q8: ret_dict={ret_dict}")
        return ret_dict
    # except (KeyError, AttributeError):
    #     print(f"r2q8e1")
    #     # This error handling is pretty rough.
    #     return {
    #         'error': 'Please submit a well-formed response.',
    #         'correct': False,
    #     }
    # except (ValueError, IndexError):
    #     print(f"r2q8e2")
    #     return {
    #         'error': 'Please submit an integer between 1 and 11 for the index.',
    #         'correct': False,
    #     }
    except:
        traceback.print_exc()

        # You may wish to provide more details or a call to action. Do you want
        # the solvers to retry, or email you?
        return {'error': 'An error occurred! Please contact the administrator.', 'correct': False}

