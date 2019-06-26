""" Davvotts RiddleBot """

import requests
from riddlebot.riddle_pybot.auth import AUTH
from string import ascii_uppercase as up_case


DOMAIN = "https://api.noopschallenge.com"
START = "/riddlebot/start"
AUTH_LOGIN = AUTH
with open("dictionary.txt") as f:
    content = f.readlines()
DICTIONARY = [word.strip() for word in content]
DICTIONARY = [word.upper() for word in DICTIONARY]

class RiddleBot:

    def __init__(self):
        # POST login to get started
        self.start = requests.post(DOMAIN + START, json={'login': AUTH_LOGIN}).json()
        self.riddle = self.start['message']
        self.riddle_path = self.start['riddlePath']
        # Get first riddle
        self.riddle_text = ""
        self.riddle_type = ""
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
            print(tested)
            if len(tested) > len(longest):
                longest = tested
                result = temp

            print(result)
        return result

    def solve_vigenere(self):
        try:
            riddleKey = self.riddle['riddleKey']
        except KeyError:
            # Key Unknown - Search Message for
            len_key = [char for char in self.riddle['message'] if char.isnumeric()]
            len_key = int(len_key[0])
            # Key is '4' elements, [1, 4, 8, 23]


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
        if msg['result'] == 'correct':
            self.riddle_path = msg['nextRiddlePath']
            self.fetch_riddle()


if __name__ == "__main__":

    testbot = RiddleBot()
    # testbot has first riddle
    reverse_solution = testbot.solve_reverse()
    testbot.post_answer(reverse_solution)

    continue_riddles = True
    while continue_riddles:
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
