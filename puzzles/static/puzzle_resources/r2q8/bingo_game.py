from flask import Flask, render_template, jsonify, request
import json
import random
import re

app = Flask(__name__)

# Global variables
word_set = set()
word_array = []
adj_set = set()
compound_word_set = set()
sub_five_letter_word_set = set()
ipa_dict = {}
animal_set = set()
last_100_word_array = []
last_100_match_array = []
understood_condition_array = []
bingo_word_array = []
input_history_string = ''

# Constants
N_COIN = 10
N_COIN_NEEDED = 1
N_COIN_NEEDED_CHEAT = 50
N_COIN_REWARD = 5

CONDITION_ARRAY = [
    '含有音标/ɪ/', '化学元素', '偶数长度', '含有E和L', '长度为6',
    'ED结尾', '含有L', '哑音B', '含有I', '去1字母成词',
    '含有Y', '含有M', '形容词', '合成词', '含有5字母词', 
    '元辅音相间', '大写字母有2个封闭区域', '含有N', '辅音比元音多1个', '动物',
    '含有T', '3个元音', '长度7或8', '国家', '含有A和E'
]

ANSWER_ARRAY = [
    'SILVER', 'CLIMBED', 'BLAMEWORTHY', 'RAVEN', 'VIETNAM',
    'TOYED', 'PLATINUM', 'DOUBTING', 'ICELAND', 'BADGER', 'METABOLIC', 'POINTY'
]

# Load data from files
def load_data():
    global word_set, word_array, adj_set, compound_word_set, sub_five_letter_word_set, ipa_dict, animal_set
    
    # Load dictionary
    with open('assets/dictionary.txt', 'r') as f:
        word_set = set(f.read().upper().split())
        word_array = list(word_set)
    
    # Load adjectives
    with open('assets/adjectives.txt', 'r') as f:
        adj_set = set(f.read().upper().split())
    
    # Load compound words
    with open('assets/compound_words.txt', 'r') as f:
        compound_word_set = set(f.read().upper().split())
    
    # Load sub five letter words
    with open('assets/sub_five_letter_words.txt', 'r') as f:
        sub_five_letter_word_set = set(f.read().upper().split())
    
    # Load IPA dictionary
    with open('assets/ipa.json', 'r') as f:
        ipa_dict = json.load(f)
    
    # Load animals
    with open('assets/animals.txt', 'r') as f:
        animal_set = set(f.read().upper().split())

def count_char(string, char):
    return string.count(char)

def has_duplicate_letters(word):
    letter_set = set()
    for char in word:
        if char in letter_set:
            return True
        letter_set.add(char)
    return False

def can_match_condition(word, index):
    vowels = 'AEIOU'
    n_vowel = sum(1 for letter in word if letter in vowels)
    n_consonant = len(word) - n_vowel

    if index == 0:  # 含有音标/ɪ/
        return word in ipa_dict and 'ɪ' in ipa_dict[word]
    
    elif index == 1:  # 化学元素
        return word.title() in CHEMICAL_ELEMENTS
    
    elif index == 2:  # 偶数长度
        return len(word) % 2 == 0
    
    elif index == 3:  # 包含E和L
        return 'E' in word and 'L' in word
    
    # ... Add all other conditions here ...
    
    return False

@app.route('/')
def index():
    return render_template('bingo.html')

@app.route('/submit', methods=['POST'])
def submit_word():
    word = request.json['word'].upper()
    
    if word == '':
        return jsonify({'success': False, 'message': '请输入单词'})
    
    if word == 'DIYBINGOCARD':
        return jsonify({
            'success': True,
            'message': 'BINGO! FDUPH账户已到账 <i class="bi bi-coin"></i> 999999999。现在给我们发送一份你自己制作的BINGO卡片吧~',
            'coin_update': 999999999
        })
    
    if not word in word_set:
        return jsonify({
            'success': False,
            'message': '我们的字典里不存在该单词'
        })
    
    # Process word matches and update game state
    match_indices = []
    for index in range(27):
        if can_match_condition(word, index):
            match_indices.append(index)
    
    # Update history
    need_update_history = word in word_set and word not in last_100_word_array
    if need_update_history:
        if len(last_100_word_array) == 100:
            last_100_word_array.pop(0)
        last_100_word_array.append(word)
        
        if len(last_100_match_array) == 100:
            last_100_match_array.pop(0)
        last_100_match_array.append(match_indices)
    
    return jsonify({
        'success': True,
        'matches': match_indices,
        'history_update': need_update_history,
        'last_matches': match_indices if need_update_history else None
    })

if __name__ == '__main__':
    load_data()
    app.run(debug=True) 