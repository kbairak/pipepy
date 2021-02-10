import itertools
import random
import sys

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        up = range(int(sys.argv[1]))
    else:
        up = itertools.count()

    try:
        for _ in up:
            a = random.randint(5, 10)
            b = random.randint(5, 10)
            question = f"{a} + {b} ?\n"
            print(question)
            answer = input()
            answer = int(answer.strip())
            if answer == a + b:
                print("Correct!")
            else:
                print("Wrong!")
    except EOFError:
        pass
