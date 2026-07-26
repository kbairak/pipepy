# PipePy to function

The function's arguments must be either:
- a subset of `returncode`, `output`, `errors`, or
- a subset of `stdout`, `stderr`

Argument ordering is irrelevant — the function's signature is inspected to assign values.

## Using output (waited execution)

In the first case, the command is waited for and its evaluated output is passed to the function.

```python
from pipepy import wc

def lines(output):
    for line in output.splitlines():
        try:
            lines, words, chars, filename = line.split()
        except ValueError:
            continue
        print(f"File {filename} has {lines} lines, "
              f"{words} words and {chars} characters")

wc('*') | lines
```

## Using stdout/stderr (streaming execution)

In the second case, the command and the function execute in parallel. The command's `stdout` and `stderr` are streamed to the function.

```python
import re
from pipepy import ping

def mean_ping(stdout):
    pings = []
    for line in stdout:
        match = re.search(r'time=([\d\.]+) ms$', line.strip())
        if not match:
            continue
        time = float(match.groups()[0])
        pings.append(time)
        if len(pings) % 10 == 0:
            print(f"Mean time is {sum(pings) / len(pings)} ms")

ping('-c', 30, "google.com") | mean_ping
```

If the command ends before the function, `next(stdout)` raises `StopIteration`. If the function ends before the command, the command's `stdin` is closed.

## Generator functions

The function can include `yield` and return a generator that can be piped into another command:

```python
from pipepy import cat, grep

def my_input():
    yield "line one\n"
    yield "line two\n"
    yield "line two\n"
    yield "something else\n"
    yield "line three\n"

def my_output(stdout):
    for line in stdout:
        yield line.upper()

print(my_input() | cat | grep('line') | my_output | grep("TWO"))
# <<< LINE TWO
# ... LINE TWO
```
