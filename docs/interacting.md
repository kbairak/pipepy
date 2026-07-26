# Interacting with background processes

There are 3 ways to interact with a background process: _read-only_, _write-only_ and _read/write_.

## 1. Incrementally sending data to a command

Piping from an iterable to a command runs the command in parallel with the iterable, feeding data as it becomes available.

```python
import random
import time
from pipepy import grep

def my_stdin():
    start = time.time()
    for _ in range(500):
        time.sleep(.01)
        yield f"{time.time() - start} {random.randint(1, 100)}\n"

command = my_stdin() | grep('-E', r'\b17$', _stream_stdout=True)
command()
```

Here, `grep` runs in parallel with the generator and matches are printed as they are found.

## 2. Incrementally reading data from a command

Iterate over a command's output to process lines as they become available.

```python
import time
from pipepy import ping

start = time.time()
for line in ping('-c', 3, 'google.com'):
    print(time.time() - start, line.strip().upper())
```

The `ping` command runs in parallel with the for-loop body; each line is delivered as it becomes available.

## 3. Reading from and writing to a command (bidirectional)

Use a `with` block for read/write interaction with a process.

```python
from pipepy import math_quiz

result = []
with math_quiz as (stdin, stdout, stderr):
    stdout = (line.strip() for line in stdout if line.strip())
    try:
        for _ in range(3):
            question = next(stdout)
            a, _, b, _ = question.split()
            answer = str(int(a) + int(b))
            stdin.write(answer + "\n")
            stdin.flush()
            verdict = next(stdout)
            result.append((question, answer, verdict))
    except StopIteration:
        pass

result
# <<< [('10 + 7 ?', '17', 'Correct!'),
# ...  ('5 + 5 ?', '10', 'Correct!'),
# ...  ('5 + 5 ?', '10', 'Correct!')]
```

`stdin`, `stdout` and `stderr` are the open file streams of the background process. When the `with` block finishes, EOF is sent to the process and it is waited for.

Remember to end lines fed to `stdin` with a newline if the command expects it, and call `stdin.flush()` as needed.

## Piping in with blocks

Call `with` on a pipe expression involving multiple `PipePy` objects. Each object's `stdout` connects to the next one's `stdin`. The `stdin` offered to the body is from the leftmost command, and `stdout`/`stderr` from the rightmost.

```python
from pipepy import cat, grep

command = cat | grep("foo") | cat | cat | cat
with command as (stdin, stdout, stderr):
    stdin.write("foo1\n")
    stdin.write("bar2\n")
    stdin.write("foo3\n")
    stdin.close()
    assert next(stdout).strip() == "foo1"
    assert next(stdout).strip() == "foo3"
```
