""" Davvotts RiddleBot """

import requests
from riddlebot.riddle_pybot.auth import AUTH
from string import ascii_uppercase as up_case
from itertools import product

DOMAIN = "https://api.noopschallenge.com"
START = "/riddlebot/start"
AUTH_LOGIN = AUTH
with open("dictionary.txt") as f:
    content = f.readlines()
DICTIONARY = [word.strip() for word in content]
DICTIONARY = [word.upper() for word in DICTIONARY]
ETAOIN = "ETAOIN" \
         "SHRDLCUMWFGYP" \
         "BVKJXQZ"

class RiddleBot:

    def __init__(self):
        # POST login to get started
        self.start = requests.post(DOMAIN + START, json={'login': AUTH_LOGIN}).json()
        self.riddle = self.start['message']
        self.riddle_path = self.start['riddlePath']
        # Get first riddle
        self.riddle_text = ""
        self.riddle_type = ""
        self.riddle_key = []
        self.riddle_master = False
        self.fetch_riddle()

    def solve_reverse(self):
        return "".join(reversed(self.riddle_text))

    def solve_rotation(self):
        text = self.riddle_text
        r = ""
        try:
            n = int(self.riddle_type.split("rot")[-1])
            r = "".join([up_case[up_case.index(c) - (26 - n)] if c != " " else c for c in text])
        except ValueError as error:
            print(error)
            return
        return r

    def solve_caesar(self):
        text = self.riddle_text
        r = ''
        try:
            n = self.riddle['riddleKey']
            r = "".join([up_case[(up_case.index(c) - n) % 26] if c != " " else c for c in text])
            return r
        except KeyError:
            pass

        # No key. Brute Force - accounting for US/ENG Dict differences
        longest = []
        result = ""
        for n in range(len(up_case)):
            temp = "".join([up_case[(up_case.index(c) - n) % 26] if c.isalpha() else c for c in text])
            tested = [word for word in temp.split() if word in DICTIONARY]
            if len(tested) > len(longest):
                longest = tested
                result = temp
        return result

    def solve_vigenere(self):
        try:
            riddleKey = self.riddle['riddleKey']
        except KeyError:
            # Key Unknown
            possible_answer = self.find_best_keys()
            return possible_answer
            # Key is '4' elements, [1, 4, 8, 23]
            # Call

        space_index = [i for i, char in enumerate(self.riddle_text) if char == " "]
        l = list("".join(self.riddle_text.split()))
        result = []
        while len(l) > 0:
            for key in riddleKey:
                try:
                    char = l.pop(0)
                    new_char = up_case[up_case.index(char) - (key)]
                    result.append(new_char)
                except IndexError:
                    pass
        for i in space_index:
            result.insert(i, " ")
        return "".join(result)

    def fetch_riddle(self):
        req = requests.get(DOMAIN + self.riddle_path)
        self.riddle = req.json()
        self.riddle_path = self.riddle['riddlePath']
        self.riddle_text = self.riddle['riddleText']
        self.riddle_type = self.riddle['riddleType']
        print(self.riddle)

    def post_answer(self, answer):
        req = requests.post(DOMAIN + self.riddle_path, json={"answer": answer})
        msg = req.json()
        print(msg)
        try:
            if msg['result'] == 'correct':
                self.riddle_path = msg['nextRiddlePath']
                self.fetch_riddle()
            elif msg['result'] == 'completed':
                self.riddle_master = True
                self.riddle_path = msg['certificate']
                print("Congratulations, you.")
                return
        except KeyError:
            pass

    def find_best_keys(self):
        text = "".join(self.riddle_text.split())
        len_key = [char for char in self.riddle['message'] if char.isnumeric()]
        len_key = int(len_key[0])
        # Split text into # sets for each supposed key
        sets = self.get_subset_strings(len_key, text)
        # Decrypt each set by -1 -> -25 (shift index of up_case)
        # pass that into get_score; scores = {shift: score}
        scores = {}
        set_to_shifts = {}
        for s in sets:
            for shift in range(26):
                # use shift to decrypt each set
                test = "".join([up_case[(up_case.index(c) - shift)] for c in s])
                score = self.get_freq_score_revised(test)
                scores[shift] = score
            # Now get highgest scoring shifts for that segment,
            highest = max(v for v in scores.values())
            potential_letter_keys = [k for (k, v) in scores.items() if v == highest]
            set_to_shifts[s] = potential_letter_keys

        # print(set_to_shifts)
        key_list = [k for k in set_to_shifts.values()]
        words_from_best_key = self.test_keys(key_list)
        return words_from_best_key

    def get_subset_strings(self, key_len, text):
        sets = []
        for i in range(key_len):
            s = "".join([char for char in text[i::key_len]])
            sets.append(s)
        return sets

    def take_first(self, item):
        return item[0]

    def get_freq_score_revised(self, text):
        # Get letter count
        letter_to_freq = {l: 0 for l in up_case}
        for char in set(text):
            letter_to_freq[char] = text.count(char)

        freq_to_letter = {}
        # Append all letters with that freq
        for letter in up_case:
            if letter_to_freq[letter] not in freq_to_letter:

                freq_to_letter[letter_to_freq[letter]] = [letter]
            else:
                freq_to_letter[letter_to_freq[letter]].append(letter)
        # Sort value chars by by ETAOIN - IMPORTANT
        for freq in freq_to_letter:
            freq_to_letter[freq].sort(key=ETAOIN.find, reverse=True)
            freq_to_letter[freq] = "".join(freq_to_letter[freq])
        # Create hashable list of tuples
        freq_tups = [(k, v) for k, v in freq_to_letter.items()]
        # Sort
        freq_tups.sort(key=self.take_first, reverse=True)
        # Extract string to count
        freq_order = "".join([v for k, v in freq_tups])
        # Count
        score = 0
        for char in ETAOIN[:6]:
            if char in freq_order[:6]:
                score += 1
        for char in ETAOIN[-6:]:
            if char in freq_order[-6:]:
                score += 1
        return score

    def test_keys(self, key_list):
        # Extract keys into list
        # keys = [k for k in set_to_shifts.values()]
        keys = key_list
        # itertools Product to get combinations if necessary
        shifts = list(product(*keys))

        # Now have a list of potential keys to plug into vigenere
        for key in shifts:
            wordiness = 0
            self.riddle['riddleKey'] = key
            test = self.solve_vigenere()
            # print(test)
            if self.score_words(test) > 10:
                return test
            elif self.score_words(test, reverse=True) > 10:
                return "".join([char for char in (reversed(test))])
        return None

    def score_words(self, words, reverse=False):
        wordiness = 0
        w = words
        if reverse:
            w = "".join([char for char in (reversed(words))])
        word_list = w.split()
        # print(word_list)
        for word in word_list:
            if word in DICTIONARY:
                wordiness += 1
            else:
                wordiness += -1
        return wordiness


if __name__ == "__main__":

    testbot = RiddleBot()
    # testbot has first riddle
    reverse_solution = testbot.solve_reverse()
    testbot.post_answer(reverse_solution)

    continue_riddles = True
    while not testbot.riddle_master:

        if "rot" in testbot.riddle_type:
            result = testbot.solve_rotation()
            testbot.post_answer(result)

        elif testbot.riddle_type == "caesar":
            result = testbot.solve_caesar()
            print(result)
            testbot.post_answer(result)

        elif testbot.riddle_type == "vigenere":
            result = testbot.solve_vigenere()
            print(result)
            testbot.post_answer(result)

    req = requests.get(DOMAIN + testbot.riddle_path)
    testbot.riddle = req.json()
    print(testbot.riddle)