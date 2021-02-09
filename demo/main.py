import random

from rich.console import Console
from rich.syntax import Syntax

from pipepy import PipePy


def rprint(text):
    syntax = Syntax(text, "python", theme="monokai")
    console = Console()
    console.print(syntax)


demo = PipePy('python', 'demo.py')
ls = PipePy('ls')
grep = PipePy('grep')
gzip = PipePy('gzip')
interactive = PipePy('python', 'interactive.py')
interactive2 = PipePy('python', 'interactive2.py')

print("# Simple command\n")
rprint("    >>> demo()")
r = demo()
rprint(f"    <<< {r!r}")
print()

print("# Iterate over results of command\n")
rprint("    >>> [name.upper() for name in ls]")
r = [name.upper() for name in ls]
rprint(f"    <<< {r!r}")
print()

print("# Pipe output of a command to another\n")
rprint("    >>> (demo | grep(2))()")
r = (demo | grep(2))()
rprint(f"    <<< {r!r}")
print()

print("# Binary mode\n")
rprint("    >>> (demo | ~gzip)()")
r = (demo | ~gzip)()
rprint(f"    <<< {r!r}")
print()

print("# Pipe string to command\n")
rprint("    >>> ('hello\\nworld' | grep('world'))()\n")
r = ('hello\nworld' | grep('world'))()
rprint(f"    <<< {r!r}")
print()

print("# Pipe iterator to command\n")
rprint("    >>> iter(['aaa\\n', 'bbb\\n']) | grep('bbb')")
r = iter(['aaa\n', 'bbb\n']) | grep('bbb')
rprint(f"    <<< {r!r}")
print()

print("# Pipe list to command\n")
rprint("    >>> ['aaa\\n', 'bbb\\n'] | grep('bbb')")
r = ['aaa\n', 'bbb\n'] | grep('bbb')
rprint(f"    <<< {r!r}")
print()

print("# Pipe command to function with string arguments\n")
rprint("    >>> def callback(returncode, output, errors):\n"
       "    ...     return returncode + 100, output.upper(), errors.upper()\n"
       "    >>> demo | callback")
r = demo | (lambda returncode, output, errors: (returncode + 100,
                                                output.upper(),
                                                errors.upper()))
rprint(f"    <<< {r!r}")
print()

print("# Pipe command to function with file arguments\n")
rprint("    >>> def callback(stdout, stderr):\n"
       "    ...     return stdout.read().upper(), stderr.read().upper()\n"
       "    >>> demo | callback")
r = demo | (lambda stdout, stderr: (stdout.read().upper(),
                                    stderr.read().upper()))
rprint(f"    <<< {r!r}")
print()

print("# Setup command to stream stderr to console and evaluate it (useful "
      "for fzf)\n")
rprint("    >>> demo(_stream_stderr=True)()")
r = demo(_stream_stderr=True)()
rprint(f"    <<< {r!r}")
print()

print("# Setup command to stream stdout to console and evaluate it (useful "
      "for dialog)\n")
rprint("    >>> demo(_stream_stdout=True)()")
r = demo(_stream_stdout=True)()
rprint(f"    <<< {r!r}")
print()

print("# Pipe command to generator\n")


code = """
    >>> def play():
    ...     result = []
    ...     try:
    ...         while True:
    ...             question = (yield)
    ...             a, plus, b, question_mark = question.split()
    ...             answer = f"{int(a) + int(b)}\\n"
    ...             verdict = (yield answer)
    ...             result.append((question, answer, verdict))
    ...     except StopIteration:
    ...         pass
    ...     return result
"""


def play():
    result = []
    try:
        while True:
            question = (yield)
            a, plus, b, question_mark = question.split()
            answer = f"{int(a) + int(b)}\n"
            verdict = (yield answer)
            result.append((question, answer, verdict))
    except StopIteration:
        pass
    return result


rprint(code)
rprint("    >>> interactive | play(result)")
r = interactive | play()
rprint(f"    <<< {r!r}")
print()


code = """
    >>> def play2():
    ...     result = []
    ...     try:
    ...         for _ in range(3):
    ...             a = random.randint(5, 10)
    ...             b = random.randint(5, 10)
    ...             question = f"{a} + {b} ?\\n"
    ...             answer = (yield question)
    ...             if int(answer.strip()) == a + b:
    ...                 verdict = "Correct!\\n"
    ...             else:
    ...                 verdict = "Wrong!\\n"
    ...             result.append((question, answer, verdict))
    ...             (yield verdict)
    ...     except StopIteration:
    ...         pass
    ...     return result
"""


def play2():
    result = []
    try:
        for _ in range(3):
            a = random.randint(5, 10)
            b = random.randint(5, 10)
            question = f"{a} + {b} ?\n"
            answer = (yield question)
            if int(answer.strip()) == a + b:
                verdict = "Correct!\n"
            else:
                verdict = "Wrong!\n"
            result.append((question, answer, verdict))
            (yield verdict)
    except StopIteration:
        pass
    return result


rprint(code)
rprint("    >>> result = []; interactive2 | play2(result); result")
r = interactive2 | play2()
rprint(f"    <<< {r!r}")
print()
