import json

with open('puzzles/puzzlehandlers/char_sample.json') as fp:
    CHAR_SAMPLE_DICT = json.load(fp)

with open('puzzles/puzzlehandlers/uncopyrightable_words.txt') as fp:
    UNCOPYRIGHTABLE_WORDS = fp.read().strip().split()
