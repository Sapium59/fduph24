import json
import logging
import random
import re
import traceback
from typing import Tuple, Dict, List, Callable
from collections import OrderedDict

from django.views.decorators.http import require_POST

from puzzles.messaging import log_puzzle_info
from ..models import Team
from .r2q8_data import SPOIL_TEXT, IPA_DICT, CHEMICAL_ELEMENTS, VOWELS, WORD_SET, ADJ_SET, ANIMAL_SET, COUNTRY_SET

logger = logging.getLogger(__name__)
SPOIL_COST = 50
BUY_A_SAMPLE_COST = 1
COIN_REWARD = 5

MILESTONE = "DIYBINGOCARD"


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
    (1,  '化学元素',    lambda word: bool(word in CHEMICAL_ELEMENTS)),
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
    (26, '恰在一条线上差一点BIJNGO', lambda word: has_almost_line(word)),
]

def get_sample_word(rule_index: int) -> str:
    if rule_index == 1:
        word = random.sample(CHEMICAL_ELEMENTS, 1)[0]
    elif rule_index == 12:
        word = random.sample(ADJ_SET, 1)[0]
    elif rule_index == 19:
        word = random.sample(ANIMAL_SET, 1)[0]
    elif rule_index == 23:
        word = random.sample(COUNTRY_SET, 1)[0]
    else:
        checker = RULES_LIST[rule_index][2]
        for trial, word in enumerate(random.sample(WORD_SET, len(WORD_SET))):
            if checker(word):
                logger.info(f"trial: {trial}")
                break
        else:
            word = "发生了些意外……请联系管理员。"
    logger.info(f"word: {word}")
    return word

# key operations
def _get_newly_known_indice(triggered_rules_indice: List[int]) -> List[int]:
    LINES = [{i + 5 * j for i in range(5)} for j in range(5)] + \
        [{j + 5 * i for i in range(5)} for j in range(5)] + \
        [{0, 6, 12, 18, 24}, {4, 8, 12, 16, 20}]
    newly_known_lines = [line for line in LINES if all(index in triggered_rules_indice for index in line)]
    newly_known_indice = set([idx for line in newly_known_lines for idx in line])
    return sorted(list(newly_known_indice))

def update(puzzle_bingo_game_data, triggered_rules_indice, guessed_word: str, max_word_history: int = 100):
    known_rules_indice: List[int] = sorted(list((puzzle_bingo_game_data["known_rules"].keys())))
    newly_known_indice: List[int] = _get_newly_known_indice(triggered_rules_indice)
    
    # update known rules
    updated_known_rules_indice = sorted(list(set(known_rules_indice + newly_known_indice)))
    puzzle_bingo_game_data["known_rules"] = {idx: RULES_LIST[idx][1] for idx in updated_known_rules_indice}
    
    # update coin num
    total_coin_reward = COIN_REWARD * len(set(newly_known_indice) - set(known_rules_indice))
    puzzle_bingo_game_data["bingo_coin_num"] += total_coin_reward

    # update history, format: "ICELAND 4,7,9,17,18,19,22,23,24,25,26,27"
    new_history_str = f"{guessed_word} {','.join([str(1+i) for i in triggered_rules_indice])}"
    if new_history_str in puzzle_bingo_game_data["word_history"]:
        puzzle_bingo_game_data["word_history"].remove(new_history_str)
    puzzle_bingo_game_data["word_history"].append(new_history_str)
    # truncate to len <= 100
    if len(puzzle_bingo_game_data["word_history"]) > max_word_history:
        puzzle_bingo_game_data["word_history"] = puzzle_bingo_game_data["word_history"][-max_word_history:]
    return puzzle_bingo_game_data


@require_POST
def submit(request):
    try:
        # get user data
        puzzle_bingo_game_data = request.context.team.puzzle_bingo_game_data
        if not puzzle_bingo_game_data:
            puzzle_bingo_game_data = team.get_default_puzzle_bingo_game_data()
        else:
            # logger.info(puzzle_bingo_game_data)
            # 数据结构改动: 版本兼容性
            if isinstance(puzzle_bingo_game_data["known_rules"], list):
                indice = puzzle_bingo_game_data["known_rules"]
            else:
                indice = list(puzzle_bingo_game_data["known_rules"].keys())
            if 25 not in indice:
                indice.append(25)
            if 26 not in indice:
                indice.append(26)
            puzzle_bingo_game_data["known_rules"] = {int(idx): RULES_LIST[int(idx)][1] for idx in indice}
            request.context.team.save()

            if puzzle_bingo_game_data["bingo_spoiled"] == True:
                puzzle_bingo_game_data["bingo_spoiled"] = SPOIL_TEXT
            # elif puzzle_bingo_game_data["bingo_spoiled"] == False:
            #     puzzle_bingo_game_data["bingo_spoiled"] = ''

        bingo_coin_num = puzzle_bingo_game_data["bingo_coin_num"]
        bingo_spoiled = puzzle_bingo_game_data["bingo_spoiled"]

        # switch case guess_a_word / do_spoil / buy_a_sample
        body = json.loads(request.body)
        mode = body.get("mode")
        logger.info(f"[I] r2q8: mode={mode}, body={body}")
        if mode == "guess_a_word":
            # submittion & rules check
            word = body.get("word", "")
            word = clear_word(word)
            if word not in WORD_SET:
                ret_dict = {
                    'error': '请参照我们提供的字典来选择单词。', 
                    'correct': True,
                    'triggered_rules': {},
                    'bingo_coin_num': bingo_coin_num,
                    'bingo_spoiled': bingo_spoiled
                }
            else:
                logger.info(f"{word} in ADJ_SET: {word in ADJ_SET}")
                triggered_rules_indice = [item[0] for item in RULES_LIST if item[2](word)]
                puzzle_bingo_game_data = update(puzzle_bingo_game_data, triggered_rules_indice, guessed_word=word)
                request.context.team.save()
                ret_dict = {
                    'error': 'BINGO! FDUPH账户已到账 999999999 金。现在给我们发送一份你自己制作的BINGO卡片吧~' if word == MILESTONE else '', 
                    'correct': True,
                    'triggered_rules': {idx: word for idx in triggered_rules_indice},  # trigger时不给rule内容，五个连成一线变成known才给
                    'bingo_coin_num': bingo_coin_num,
                    'bingo_spoiled': bingo_spoiled
                }
        elif mode == "do_spoil":
            if bingo_coin_num >= SPOIL_COST and not bingo_spoiled:
                puzzle_bingo_game_data["bingo_spoiled"] = SPOIL_TEXT
                puzzle_bingo_game_data["bingo_coin_num"] -= SPOIL_COST
                request.context.team.save()
                ret_dict = {
                    'error': '', 
                    'spoil_text': SPOIL_TEXT,
                    'correct': True,
                    'triggered_rules': {},
                    'bingo_coin_num': bingo_coin_num,
                    'bingo_spoiled': bingo_spoiled
                }
            elif bingo_spoiled:
                err_msg = f'你已经暗箱操作过了！'
                ret_dict = {
                    'error': err_msg,
                    'correct': True,
                    'triggered_rules': {},
                    'bingo_coin_num': bingo_coin_num,
                    'bingo_spoiled': bingo_spoiled
                }
            else:
                err_msg = f'你没有足够的奖金来暗箱操作（需要{SPOIL_COST}）'
                ret_dict = {
                    'error': err_msg,
                    'correct': True,
                    'triggered_rules': {},
                    'bingo_coin_num': bingo_coin_num,
                    'bingo_spoiled': bingo_spoiled
                }
        elif mode == "buy_a_sample":
            if bingo_coin_num < BUY_A_SAMPLE_COST:
                ret_dict = {
                    'error': '请先凭借智慧积累一些财富吧……',
                    'correct': True,
                    'sample_word': '',
                    'bingo_coin_num': bingo_coin_num,
                    'bingo_spoiled': bingo_spoiled
                }
            elif 'rule_index' in body and isinstance(body['rule_index'], int) and 0 <= body['rule_index'] <= 26:
                sample_word = get_sample_word(body['rule_index'])
                puzzle_bingo_game_data["bingo_coin_num"] -= BUY_A_SAMPLE_COST
                request.context.team.save()
                ret_dict = {
                    'error': '',
                    'correct': True,
                    'sample_word': sample_word,
                    'bingo_coin_num': bingo_coin_num,
                    'bingo_spoiled': bingo_spoiled
                }
            else:
                ret_dict = {
                    'error': '发生未知错误，请联系管理员。',
                    'correct': True,
                    'sample_word': '',
                    'bingo_coin_num': bingo_coin_num,
                    'bingo_spoiled': bingo_spoiled
                }
        else:
            logger.info(f"Warning: unknown mode in r2q8: {mode}")
            ret_dict = {'error': '发生未知错误，请联系管理员。'}

        # when no error, ret_dict['error'] must be empty
        # ret_dict['error'] = ''
        # logger.info(f"[I] r2q8: ret_dict={ret_dict}")
        return ret_dict
    except:
        logger.info(traceback.format_exc())
        return {
            'error': '发生未知错误，请联系管理员。',
            'correct': True,
            'triggered_rules': {},
            'bingo_coin_num': bingo_coin_num,
            'bingo_spoiled': bingo_spoiled
        }

