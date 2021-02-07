import random

from rich.console import Console
from rich.syntax import Syntax

from pipepy import PipePy


def rprint(text):
    syntax = Syntax(text, "python", theme="monokai")
    console = Console()
    console.print(syntax)


demo = PipePy('python', 'demo.py')
grep = PipePy('grep')
interactive = PipePy('python', 'interactive.py')
interactive2 = PipePy('python', 'interactive2.py')

print("# Simple command\n")
r = demo()
rprint(f"    >>> demo()\n    <<< {r!r}")
print()

print("# Pipe output of a command to another\n")
r = (demo | grep('2'))()
rprint(f"    >>> (demo | grep('2'))()\n    <<< {r!r}")
print()

print("# Pipe string to command\n")
r = (b'hello\nworld' | grep('world'))()
rprint(f"    >>> (b'hello\\nworld' | grep('world'))()\n    <<< {r!r}")
print()

print("# Pipe iterator to command\n")
r = iter([b'aaa\n', b'bbb\n']) | grep('bbb')
rprint(f"    >>> iter([b'aaa\\n', b'bbb\\n']) | grep('bbb')\n"
       f"    <<< {r!r}")
print()

print("# Pipe list to command\n")
r = [b'aaa\n', b'bbb\n'] | grep('bbb')
rprint(f"    >>> [b'aaa\\n', b'bbb\\n'] | grep('bbb')\n"
       f"    <<< {r!r}")
print()

print("# Pipe command to function\n")
r = demo | (lambda returncode, stdout, stderr: (returncode + 100,
                                                stdout.upper(),
                                                stderr.upper()))
rprint(f"    >>> def callback(returncode, stdout, stderr):\n"
       f"    ...     return returncode + 100, stdout.upper(), stderr.upper()\n"
       f"    >>> demo | callback\n"
       f"    <<< {r!r}")
print()

print("# Pipe command to function (with keyword arguments)\n")
r = demo | (lambda **kwargs: kwargs)
rprint(f"    >>> demo | (lambda **kwargs: kwargs)\n"
       f"    <<< {r!r}")
print()

print("# Setup command to stream stderr to console and evaluate it\n")
rprint("    >>> (~ demo)()")
r = (~ demo)()
rprint(f"    <<< {r!r}")
print()

print("# Setup command to stream stdout to console and evaluate it\n")
rprint("    >>> (~~ demo)()")
r = (~~ demo)()
rprint(f"    <<< {r!r}")
print()

print("# Pipe command to generator\n")


code = """
    >>> def play(result):
    ...     try:
    ...         while True:
    ...             question = yield
    ...             a, plus, b, question_mark = question.split()
    ...             answer = f"{int(a) + int(b)}\\n".encode('utf8')
    ...             verdict = yield answer
    ...             result.append((question, answer, verdict))
    ...     except StopIteration:
    ...         pass
"""


def play(result):
    try:
        while True:
            question = yield
            a, plus, b, question_mark = question.split()
            answer = f"{int(a) + int(b)}\n".encode('utf8')
            verdict = yield answer
            result.append((question, answer, verdict))
    except StopIteration:
        pass


rprint(code)
rprint("    >>> result = []; interactive | play(result); result")
r = result = []
interactive | play(result)
result
rprint(f"    <<< {r!r}")
print()


code = """
    >>> def play2(reuslt):
    ...     for _ in range(3):
    ...         a = random.randint(5, 10)
    ...         b = random.randint(5, 10)
    ...         question = f"{a} + {b} ?\\n".encode('utf8')
    ...         answer = yield question
    ...         if int(answer.strip()) == a + b:
    ...             verdict = b"Correct!\\n"
    ...         else:
    ...             verdict = b"Wrong!\\n"
    ...         result.append((question, answer, verdict))
    ...         yield verdict
"""


def play2(reuslt):
    for _ in range(3):
        a = random.randint(5, 10)
        b = random.randint(5, 10)
        question = f"{a} + {b} ?\n".encode('utf8')
        answer = yield question
        if int(answer.strip()) == a + b:
            verdict = b"Correct!\n"
        else:
            verdict = b"Wrong!\n"
        result.append((question, answer, verdict))
        yield verdict

rprint(code)
rprint("    >>> result = []; interactive2 | play2(result); result")
result = []
interactive2 | play2(result)
result
rprint(f"    <<< {r!r}")
print()
