import json
import random
import re
import traceback
from typing import Tuple, Dict, List, Callable, Literal
from collections import OrderedDict

from django.views.decorators.http import require_POST

from puzzles.messaging import log_puzzle_info
from puzzles.utils import get_default_puzzle_genshin_game_data
from ..models import Team
from .r3q3_data import CHAR_SAMPLE_DICT, UNCOPYRIGHTABLE_WORDS




def get_poem() -> Dict[str, str]:
    """ 错乱诗 """
    rnd_char_list = [random.choice(CHAR_SAMPLE_DICT[str(idx)]) for idx in range(15)]
    rnd_char_list[7] = '，'
    rnd_char_list[13] = '?'
    poem = ''.join(rnd_char_list)
    return {poem: "错乱诗"}


def get_freq() -> Dict[str, str]:
    """ 多频段 """
    freq = random.choice(UNCOPYRIGHTABLE_WORDS)
    return {freq: "多频段"}


def get_prob() -> Dict[str, str]:
    """ 概率数 """
    cumulative_prob_array = [0, .06, .24, .29, .46, .67, .72, .75, 1]
    result_array = [1, 2, 3, 4, 5, 6, 8, 9]
    prob = random.choices(result_array, cum_weights=cumulative_prob_array[1:])[0]
    return {prob: "概率数"}


def get_bell() -> Dict[str, str]:
    """ 高斯钟 """
    def _c2i(letter:str) -> int:
        """ A, a -> 0 """
        return ord(letter.upper()) - 65
    def _i2c(i:int) -> str:
        """ 0 -> A """
        return chr(65+i)
    def _bell_rnd(mu, sigma) -> int:
        rnd = random.normalvariate(mu, sigma)
        rnd = int(rnd)
        rnd = max(rnd, 0)
        rnd = min(rnd, 25)
        return rnd
    def _get_bell(letter:str, sigma: float) -> str:
        mu = _c2i(letter)
        i = _bell_rnd(mu, sigma)
        return _i2c(i)
    mean = "JACKPOT"
    bell = "?"
    for letter in "ACKPOT":
        bell += _get_bell(letter, sigma=1.5)
    return {bell: "高斯钟"}


def get_wndw() -> Dict[str, str]:
    """ 观测窗 """
    src = ['S', 'A', 'M', 'P', 'L', 'I', '_', 'G']
    show_idx = random.choice(list(range(len(src))))
    show_str = ' '.join(['_' if idx != show_idx else src[idx] for idx in range(len(src))])
    return {show_str: "观测窗"}


def get_one() -> Dict[str, Literal['poem', 'freq', 'prob', 'bell', 'wndw']]:
    funcs = [get_poem, get_bell, get_wndw, get_prob, get_freq ]
    weights = [2,4,1,3,5]
    func = random.choices(funcs, weights=weights)[0]
    return func()



@require_POST
def submit(request):
    try:
        # get user data
        puzzle_genshin_game_data = request.context.team.puzzle_genshin_game_data
        if not puzzle_genshin_game_data:
            puzzle_genshin_game_data = get_default_puzzle_genshin_game_data()

        body = json.loads(request.body)
        get_num = body.get("num")
        if get_num not in [1, 10]:
            raise ValueError('Expect get num to be 1 or 10.')
        if len(puzzle_genshin_game_data["history"]) >= 2000:
            return {
                'error': '你并不需要那么多次抽取来解决本题。', 
                'correct': True,
            }

        new_items = [get_one() for _ in range(get_num)]
        puzzle_genshin_game_data["history"].extend(new_items)
        new_items_text = [list(item.keys())[0] for item in new_items]
        request.context.team.save()
        return {
            'error': '', 
            'correct': True,
            'new_items_text': new_items, #_text,
        }
    except:
        traceback.print_exc()

        # You may wish to provide more details or a call to action. Do you want
        # the solvers to retry, or email you?
        return {'error': '发生未知错误，请联系管理员。', 'correct': False}

