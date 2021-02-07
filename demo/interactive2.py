if __name__ == "__main__":
    while True:
        try:
            question = input("")
        except EOFError:
            break
        a, plus, b, question_mark = question.split()
        answer = f"{int(a) + int(b)}\n"
        print(answer)
        verdict = input("")
