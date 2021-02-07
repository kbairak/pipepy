import random

if __name__ == "__main__":
    for _ in range(3):
        a = random.randint(5, 10)
        b = random.randint(5, 10)
        print(f"{a} + {b} ?")
        answer = int(input())
        if answer == a + b:
            print("Correct!")
        else:
            print("Wrong!")
