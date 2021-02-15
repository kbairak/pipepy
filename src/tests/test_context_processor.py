import itertools
import random
from copy import copy

from pipepy import PipePy, cat, grep

student_command = PipePy('python', 'src/tests/playground/math_quiz_student.py')
teacher_command = PipePy('python', 'src/tests/playground/math_quiz_teacher.py')


def python_student(stdin, stdout, up):
    """ Interacts with stdin and stdout as a student to a math quiz

        `up` should either be `range(X)` or `itertools.count()`
    """

    result = []
    stdout = (line.strip() for line in iter(stdout) if line.strip())
    try:
        for _ in up:
            question = next(stdout)
            a, _, b, _ = question.split()
            answer = f"{int(a) + int(b)}\n"
            stdin.write(answer)
            stdin.flush()
            verdict = next(stdout)
            result.append((question, answer, verdict))
    except StopIteration:
        pass
    return result


def python_teacher(stdin, stdout, up):
    """ Interacts with stdin and stdout as a teacher to a math quiz

        `up` should either be `range(X)` or `itertools.count()`
    """

    # `up` should either be `range(X)` or `itertools.count()`
    result = []
    stdout = (line.strip() for line in iter(stdout) if line.strip())
    try:
        for _ in up:
            a = random.randint(5, 10)
            b = random.randint(5, 10)
            question = f"{a} + {b} ?\n"
            stdin.write(question)
            stdin.flush()
            answer = next(stdout)
            answer = int(answer.strip())
            if answer == a + b:
                verdict = "Correct!\n"
            else:
                verdict = "Wrong!\n"
            stdin.write(verdict)
            stdin.flush()
            result.append((question, answer, verdict))
    except StopIteration:
        pass
    return result


def test_math_quiz_teacher_python_stops_first():
    with teacher_command as (stdin, stdout, stderr):
        result = python_student(stdin, stdout, range(3))

    assert len(result) == 3
    assert [verdict.strip() for _, _, verdict in result] == ["Correct!"] * 3


def test_math_quiz_teacher_command_stops_first():
    with teacher_command(3) as (stdin, stdout, stderr):
        result = python_student(stdin, stdout, itertools.count())

    assert len(result) == 3
    assert [verdict.strip() for _, _, verdict in result] == ["Correct!"] * 3


def test_math_quiz_student_python_stops_first():
    with student_command as (stdin, stdout, stderr):
        result = python_teacher(stdin, stdout, range(3))

    assert len(result) == 3
    assert [verdict.strip() for _, _, verdict in result] == ["Correct!"] * 3


def test_math_quiz_student_command_stops_first():
    with student_command(3) as (stdin, stdout, stderr):
        result = python_teacher(stdin, stdout, itertools.count())

    assert len(result) == 3
    assert [verdict.strip() for _, _, verdict in result] == ["Correct!"] * 3


def test_inspect_result():
    job = copy(teacher_command)
    with job as (stdin, stdout, stderr):
        python_student(stdin, stdout, range(3))

    assert job


def test_long_pipe():
    result = []
    with (cat | grep("foo") | cat | cat | grep("foo") | cat) as (
            stdin, stdout, stderr):
        stdin.write("bar\n")
        stdin.write("foo\n")
        stdin.close()
        result.append(next(stdout).strip())
    assert result == ["foo"]
