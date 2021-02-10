import itertools
import sys

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        up = range(int(sys.argv[1]))
    else:
        up = itertools.count()

    try:
        for _ in up:
            question = input()
            a, _, b, _ = question.split()
            a = int(a)
            b = int(b)
            answer = str(a + b)
            print(answer)
            verdict = input()
    except EOFError:
        pass
