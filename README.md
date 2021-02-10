A Python library for invoking and interacting with shell commands.

![Build](https://github.com/kbairak/pipepy/workflows/Test%20suite/badge.svg)

## Table of contents

<!--ts-->
* [Why? Comparison with other similar frameworks](#why-comparison-with-other-similar-frameworks)
* [Installation and testing](#installation-and-testing)
* [Intro, basic usage](#intro-basic-usage)
* [Laziness](#laziness)
* [Customizing commands](#customizing-commands)
* [Redirecting output to files](#redirecting-output-to-files)
* [Pipes](#pipes)
   * [1. Both operands are commands](#1-both-operands-are-commands)
   * [2. Left operand is a string](#2-left-operand-is-a-string)
   * [3. Left operand is any kind of iterable](#3-left-operand-is-any-kind-of-iterable)
   * [4. Right operand is a function](#4-right-operand-is-a-function)
* [Running in the background](#running-in-the-background)
   * [1. Incrementally sending data to a command](#1-incrementally-sending-data-to-a-command)
   * [2. Incrementally reading data from a command](#2-incrementally-reading-data-from-a-command)
   * [3. Reading data from and writing data to a command](#3-reading-data-from-and-writing-data-to-a-command)
* [Binary mode](#binary-mode)
* [Streaming to console](#streaming-to-console)
* [Utils](#utils)
* ["Interactive" mode](#interactive-mode)
* [TODOs](#todos)

<!-- Added by: kbairak, at: Wed Feb 10 12:13:31 PM EET 2021 -->

<!--te-->

## Why? Comparison with other similar frameworks

1. **[Xonsh](https://xon.sh/)**: Xonsh allows you to combine shell and Python
   and enables very powerful scripting and interactive sessions. This library
   does the same to a limited degree. However, Xonsh introduces a new language
   that is a superset of Python. The main goal of this library that sets it
   apart is that it is intended to be a pure Python implementation, mainly
   aimed at scripting.

2. **[sh](https://github.com/amoffat/sh)** and
   **[pieshell](https://github.com/redhog/pieshell)**: These are much closer to
   the current library in that they are pure Python implementations. The
   current library, however, tries to improve on the following aspects:

   - It tries to apply more syntactic sugar to make the invocations feel more
     like shell invocations.

   - It tries to offer ways to have shell commands interact with python code in
     powerful and intuitive ways.

## Installation and testing

```sh
python -m pip install pipepy

```

Or, if you want to modify the code while trying it out:

```sh
git clone https://github.com/kbairak/pipepy
cd pipepy
python -m pip install  -e .
```

To run the tests, you need to first install the testing requirements:

```sh
python -m pip install -r test_requirements.txt

make test
# or
pytest
```

There are a few more `make` targets to assist with testing during development:

- `covtest`: Produces and opens a coverage report
- `watchtest`: Listens for changes in the source code files and reruns the
  tests automatically
- `debugtest`: Runs the tests without capturing their output so that you can
  insert a debug statement

## Intro, basic usage

```python
from pipepy import ls, grep

print(ls)  # prints contents of current folder
if ls | grep('info.txt'):
      print('info.txt found')
```

Most shell commands are importable straight from the `pipepy` module. Dashes in
commands' names are converted to underscore (`docker-compose` →
`docker_compose`). Commands that cannot be found automatically can be created
with the PipePy constructor:

```python
from pipepy import PipePy

custom_command = PipePy('./bin/custom')
python_script = PipePy('python', 'script.py')
```

## Laziness

Commands are evaluated lazily. For example, this will not actually do anything:

```python
from pipepy import wget
wget('http://...')
```

A command will be evaluated when its output is used. This can be done with the
following ways:

- Accessing the `returncode`, `stdout` and `stderr` properties

- Evaluating the command as a boolean object:

  ```python
  from pipepy import ls, grep
  if ls | grep('info.txt'):
      print("info.txt found")
  ```

  The command will be truthy if its `returncode` is 0.

- Evaluating the command as a string object

  ```python
  from pipepy import ls
  result = str(ls)
  # or
  print(ls)
  ```

  Converting a command to a `str` returns its `stdout`.

- Invoking the `.as_table()` method:

  ```python
  from pipepy import ps
  ps.as_table()
  # <<< [{'PID': '11233', 'TTY': 'pts/4', 'TIME': '00:00:01', 'CMD': 'zsh'},
  # ...  {'PID': '17673', 'TTY': 'pts/4', 'TIME': '00:00:08', 'CMD': 'ptipython'},
  # ...  {'PID': '18281', 'TTY': 'pts/4', 'TIME': '00:00:00', 'CMD': 'ps'}]
  ```

- Iterating over a command object:

  This iterates over the lines of the command's `stdout`:

  ```python
  from pipepy import ls
  for filename in ls:
      print(filename.upper)
  ```

  `command.iter_words()` iterates over the words of the command's `stdout`:

  ```python
  from pipepy import ps
  list(ps.iter_words())
  # <<< ['PID', 'TTY', 'TIME', 'CMD',
  # ...  '11439', 'pts/5', '00:00:00', 'zsh',
  # ...  '15532', 'pts/5', '00:00:10', 'ptipython',
  # ...  '15539', 'pts/5', '00:00:00', 'ps']
  ```

- Redirecting the output to something else (this will be further explained
  below):

  ```python
  from pipepy import ls, grep
  ls > 'files.txt'
  ls >> 'files.txt'
  ls | grep('info.txt')  # `ls` will be evaluated, `grep` will not
  ls | lambda output: output.upper()
  ```

- Redirecting from an iterable (this will be further explained below):

  ```python
  from pipepy import grep
  (f"{i}\n" for i in range(5)) | grep(2)
  ```

- Setting the command to run in the background (this will be further explained
  below):

  ```python
  download = -wget('http://...')
  # Do something else in the meantime
  download.wait()
  if download:
      print("Download was successful")
  else:
      print("Download was successful")

  ```

If you are not interested in the output of a command but want to evaluate it
nevertheless, you can call it with empty arguments. So, this will actually
invoke the command (and wait for it to finish).

```python
from pipepy import wget
wget('http://...')()
```

## Customizing commands

Calling a command with non empty arguments will return a modified unevaluated
copy. So the following are equivalent:

```python
from pipepy import PipePy
ls_l = PipePy('ls', '-l')
# Is equivalent to
ls_l = PipePy('ls')('-l')
```

There is a number of other ways you can customize a command:

- **Globs**: globbing will be applied to all positional arguments:

  ```python
  from pipepy import echo
  print(echo('*'))  # Will print all files in the current folder
  ```

  You can use `glob.escape` if you want to avoid this functionality:

  ```python
  import glob
  from pipepy import ls, echo

  print(ls)
  # <<< **a *a *aa

  print(echo('*a'))
  # <<< **a *a *aa

  print(echo(glob.escape('*a')))
  # <<< *a
  ```

- **Keyword arguments**:

  ```python
  from pipepy import ls
  ls(sort="size")     # Equivalent to ls('--sort=size')
  ls(sort_by="size")  # Equivalent to ls('--sort-by=size')
  ls(escape=True)     # Equivalent to ls('--escape')
  ls(escape=False)    # Equivalent to ls('--no-escape')
  ```

  Since keyword arguments come after positional arguments, if you want the
  final command to have a different ordering you can invoke the command
  multiple times:

  ```python
  from pipepy import ls
  ls('-l', sort="size")  # Equivalent to ls('-l', '--sort=size')
  ls(sort="size")('-l')  # Equivalent to ls('--sort=size', '-l')
  ```

- **Attribute access**:

  ```python
  from pipepy import git
  git.push.origin.bugfixes  # Equivalent to git('push', 'origin', 'bugfixes')
  ```

- **Minus sign**:

  ```python
  from pipepy import ls
  ls - 'l'        # Equivalent to ls('-l')
  ls - 'default'  # Equivalent to ls('--default')
  ```

  This is to enable making the invocations look more like the shell:

  ```python
  from pipepy import ls
  l, t = 'l', 't'
  ls -l -t  # Equivalent to ls('-l', '-t')
  ```

  You can call `pipepy.overload_chars(locals())` in your script to assign all
  ascii letters to variables of the same name.

  ```python
  from pipepy import ls, overload_chars
  overload_chars(locals())
  ls -l -t  # Equivalent to ls('-l', '-t')
  ```

## Redirecting output to files

The `>`, `>>` and `<` operators work similar to how they work in a shell:

```python
ls               >  'files.txt'  # Will overwrite files.txt
ls               >> 'files.txt'  # Will append to files.txt
grep('info.txt') <  'files.txt'  # Will use files.txt as input
```

## Pipes

The `|` operator is used to customize where a command gets its input from and
what it does with its output. Depending on the types of the operands, different
behaviors will emerge:

### 1. Both operands are commands

If both operands are commands, the result will be as similar as possible to
what would have happened in a shell:

```python
from pipepy import git, grep
if git.diff(name_only=True) | grep('readme.txt'):
      print("readme was changed")
```

If the left operand was previously evaluated, then it's output (`stdout` and
`stderr`) will be passed directly as inputs to the right operand. Otherwise,
both commands will be executed in parallel and `left`'s output will be streamed
into `right`.

### 2. Left operand is a string

If the left operand is a string, it will be used as the command's stdin:

```python
from pipepy import grep
result = "John is 18 years old\nMary is 25 years old" | grep("Mary")
print(result)
# <<< Mary is 25 years old
```

### 3. Left operand is any kind of iterable

If the left operand is any kind of iterable, its elements will be fed to the
command's stdin one by one:

```python
import random
from pipepy import grep

result = ["John is 18 years old\n", "Mary is 25 years old"] | grep("Mary")
print(result)
# <<< Mary is 25 years old

def my_stdin():
      for _ in range(500):
            yield f"{random.randint(1, 100)}\n"

result = my_stdin() | grep(17)
print(result)
# <<< 17
# ... 17
# ... 17
# ... 17
# ... 17
```

### 4. Right operand is a function

The function's arguments need to either be:

- a subset of `returncode`, `output`, `errors` or
- a subset of `stdout`, `stderr`

The ordering of the arguments is irrelevant since the function's signature will
be inspected to assign the proper values.

In the first case, the command will be waited for and its evaluated output will
be made available to the function's arguments.

```python
from pipepy import wc

def lines(output):
    for line in output.splitlines():
        try:
            lines, words, chars, filename = line.split()
        except ValueError:
            continue
        print(f"File {filename} has {lines} lines, {words} words and {chars} "
              "characters")

wc('*') | lines
# <<< File demo.py has 6 lines, 15 words and 159 characters
# ... File main.py has 174 lines, 532 words and 4761 characters
# ... File interactive2.py has 10 lines, 28 words and 275 characters
# ... File interactive.py has 12 lines, 34 words and 293 characters
# ... File total has 202 lines, 609 words and 5488 characters
```

In the second case, the command will be executed in the background and its
`stdout` and `stderr` streams will be made available to the function.

```python
import re
from pipepy import ping

def mean_ping(stdout):
    pings = []
    lines = iter(stdout)
    while True:
        try:
            line = next(lines)
        except StopIteration:
            break
        match = re.search(r'time=([\d\.]+) ms$', line.strip())
        if not match:
            continue
        time = float(match.groups()[0])
        pings.append(time)
        if len(pings) % 10 == 0:
            print(f"Mean time is {sum(pings) / len(pings)} ms")

ping('-c', 30, "google.com") | mean_ping
# >>> Mean time is 71.96000000000001 ms
# ... Mean time is 72.285 ms
# ... Mean time is 72.19666666666667 ms
```

## Running in the background

You can run commands in the background by prepending `-` to them. At a later
point you can wait for them to finish with `.wait()`.

```python
import time
from pipepy import sleep

def main():
   start = time.time()

   print(f"Starting background process at {time.time() - start}")
   result = -sleep(3)

   print(f"Printing message at {time.time() - start}")

   print(f"Waiting for 1 second in python at {time.time() - start}")
   time.sleep(1)

   print(f"Printing message at {time.time() - start}")

   print(f"Waiting for process to finish at {time.time() - start}")
   result.wait()

   print(f"Process finished at {time.time() - start}")

main()
# <<< Starting background process    at 0.0000004768371582031
# ... Printing message               at 0.0027723312377929688
# ... Waiting for 1 second in python at 0.0027921199798583984
# ... Printing message               at 1.0040225982666016
# ... Waiting for process to finish  at 1.0040972232818604
# ... Process finished               at 3.004188776016235
```

**Interracting with background processes**

There are 3 ways to interact with a background process: _read-only_,
_write-only_ and _read/write_. We have already covered _read-only_ and
_write-only_:

### 1. Incrementally sending data to a command

This is done by piping from an iterable to a command. The command actually runs
in the background and the iterable's data is fed to it as it becomes available.
We will slightly modify the previous example to better demonstrate this:

```python
import random
import time
from pipepy import grep

def my_stdin():
    start = time.time()
    for _ in range(500):
        time.sleep(.01)
        yield f"{time.time() - start} {random.randint(1, 100)}\n"

my_stdin() | grep('-E', r'\b17$', _stream_stdout=True)
# <<< 0.3154888153076172 17
# ... 1.5810892581939697 17
# ... 1.7773401737213135 17
# ... 2.8303775787353516 17
# ... 3.4419643878936768 17
# ... 4.511774301528931  17
```

Here, `grep` is actually run in the background and matches are printed as they
are found since the command's output is being streamed to the console, courtesy
of the `_stream_stdout` argument (more on this [below](#streaming-to-console)).

### 2. Incrementally reading data from a command

This can be done by iterating over a command's output:

```python
import time
from pipepy import ping

start = time.time()
for line in ping('-c', 3, 'google.com'):
    print(time.time() - start, line.strip().upper())
# <<< 0.15728354454040527 PING GOOGLE.COM (172.217.169.142) 56(84) BYTES OF DATA.
# ... 0.1574106216430664  64 BYTES FROM SOF02S32-IN-F14.1E100.NET (172.217.169.142): ICMP_SEQ=1 TTL=103 TIME=71.8 MS
# ... 1.1319730281829834  64 BYTES FROM 142.169.217.172.IN-ADDR.ARPA (172.217.169.142): ICMP_SEQ=2 TTL=103 TIME=75.3 MS
# ... 2.1297826766967773  64 BYTES FROM 142.169.217.172.IN-ADDR.ARPA (172.217.169.142): ICMP_SEQ=3 TTL=103 TIME=73.4 MS
# ... 2.129857063293457
# ... 2.129875659942627   --- GOOGLE.COM PING STATISTICS ---
# ... 2.1298911571502686  3 PACKETS TRANSMITTED, 3 RECEIVED, 0% PACKET LOSS, TIME 2004MS
# ... 2.129910707473755   RTT MIN/AVG/MAX/MDEV = 71.827/73.507/75.253/1.399 MS
```

Again, the `ping` command is actually run in the background and each line is
given to the body of the for-loop as it becomes available.

Another way is to pipe the command to a function that has a subset of `stdin`
and `stdout` as its arguments, as we demonstrated
[before](#4-right-operand-is-a-function).

### 3. Reading data from and writing data to a command

Lets assume we have a command that makes the user take a math quiz. A normal
interaction with this command would look like this:

```
→ math_quiz
3 + 4 ?
→ 7
Correct!
8 + 2 ?
→ 12
Wrong!
→ Ctrl-d
```

Using python to interact with this command in a read/write fashion can be done
with a `with` statement:

```python
from pipepy import math_quiz

result = []
with math_quiz as (stdin, stdout, stderr):
    stdout = (line.strip() for line in stdout if line.strip())
    try:
        for _ in range(3)
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

`stdin`, `stdout` and `stderr` are the open file streams of the background
process. When the body of the `with` block finishes, an EOF is sent to the
process and it is waited for.

You need to remember to end lines fed to `stdin` with a newline character if
the command expects it. Also, don't forget to call `stdin.flush()` every now
and then.

If you want to capture the `returncode` of the command after the `with` block
finishes, you must call it on a background command, which will have been waited
for when the block ends:


```python
from pipepy import math_quiz

command = -math_quiz

with command as (stdin, stdout, stderr):
    ...

if command:  # No need to `command.wait()`
    print("Math quiz successful")
else:
    print("Math quiz failed")
```

## Binary mode

All commands are executed in text mode, which means that they deal with `str`
objects. This can cause problems. For example:

```python
from pipepy import gzip
result = "hello world" | gzip
print(result.stdout)
# <<< Traceback (most recent call last):
# ... ...
# ... UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8b in position 1: invalid start byte
```

`gzip` cannot work in text mode because its output is binary data that cannot
be utf-8-decoded. When text mode is not desirable, a command can be converted
to binary mode by prepending the `~` operator:

```python
from pipepy import gzip
result = "hello world" | ~gzip
print(result.stdout)
# <<< b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\xcbH\xcd\xc9\xc9W(\xcf/\xcaI\xe1\x02\x00-;\x08\xaf\x0c\x00\x00\x00'
```

Input and output will be converted from/to binary by using the 'UTF-8'
encoding. In the previous example, our input's type was `str` and was
utf-8-encoded before being fed into `gzip`. You can change the encoding with
the `_encoding` keyword argument:

```python
from pipepy import gzip
result = "καλημέρα" | ~gzip
print(result.stdout)
# <<< b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\x01\x10\x00\xef\xff\xce\xba\xce\xb1\xce\xbb\xce\xb7\xce\xbc\xce\xad\xcf\x81\xce\xb1"\x15g\xab\x10\x00\x00\x00'
result = "καλημέρα" | ~gzip(_encoding="iso-8859-7")
print(result.stdout)
# <<< b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03{\xf5\xf0\xf5\xf37w?>\x04\x00\x1c\xe1\xc0\xf7\x08\x00\x00\x00'
```

## Streaming to console

During invocation, you can set the `_stream_stdout` and `_stream_stderr`
keyword arguments to `True`. This means that the respective stream will not be
captured by the result, but streamed to the console. This allows the user to
interact with interactive commands. Consider the following 2 examples:

1. **[fzf](https://github.com/junegunn/fzf)** works like this:

   1. It gathers a list of choices from its `stdin`
   2. It displays the choices on `stderr`, constantly refreshing it depending
      on what the user inputs
   3. It starts directly capturing keystrokes on the keyboard, bypassing
      `stdin`, to allow the user to make their choice.
   4. When the user presses Enter, it prints the choice to its `stdout`

   Taking all this into account, we can do the following:

   ```python
   from pipepy import fzf
   fzf = fzf(_stream_stderr=True)

   # This will open an fzf session to let us choose between "John" and "Mary"
   print("John\nMary" | fzf)
   # <<< Mary
   ```

2. **[dialog](https://invisible-island.net/dialog/)** works similar to `fzf`,
   but swaps `stdout` with `stderr`:

   1. It gathers a list of choices from its arguments
   2. It displays the choices on `stdout`, constantly refreshing it depending
      on what the user inputs
   3. It starts directly capturing keystrokes on the keyboard, bypassing
      `stdin`, to allow the user to make their choice.
   4. When the user presses Enter, it prints the choice to its `stderr`

   Taking all this into account, we can do the following:

   ```python
   from pipepy import dialog
   dialog = dialog(_stream_stdout=True)

   # This will open a dialog session to let us choose between "John" and "Mary"
   result = dialog(checklist=True)('Choose name', 30, 110, 0,
                                   "John", '', "on",
                                   "Mary", '', "off")
   print(result.stderr)
   # <<< John
   ```

Also, during a script, you may not be interested in capturing the output of a
command but may want to stream it to the console to show the command's output
to the user. A shortcut for setting both `_stream_stdout` and `_stream_stderr`
to `True` is the `+` sign:

```python
from pipepy import wget

(+wget('https://...'))()
```

While `stdout` and `stderr` will not be captured, `returncode` will and thus
you can still use the command in boolean expressions:

```python
from pipepy import wget

if +wget('https://...'):
     print("Download succeeded")
else:
     print("Download failed")
```

## Utils

Since changing the current working directory or the environment in a subprocess
has no effect on the current process, we include the `pipepy.cd` and
`pipepy.export` functions. These are not `PipePy` instances but simple aliases
to `os.chdir` and `os.environ.__setitem__` respectively.

## "Interactive" mode

When "interactive" mode is set, the `__repr__` method will simply return
`self.stdout + self.stderr`. This enables some very basic functionality for the
interactive python shell. To set interactive mode, run
`pipepy.set_interactive(True)`:

```python
from pipepy import ls, set_interactive, overload_chars
set_interactive(True)
ls
# <<< demo.py
# ... interactive2.py
# ... interactive.py
# ... main.py

overload_chars(locals())
ls -l
# <<< total 20
# ... -rw-r--r-- 1 kbairak kbairak  159 Feb  7 22:05 demo.py
# ... -rw-r--r-- 1 kbairak kbairak  275 Feb  7 22:04 interactive2.py
# ... -rw-r--r-- 1 kbairak kbairak  293 Feb  7 22:04 interactive.py
# ... -rw-r--r-- 1 kbairak kbairak 4761 Feb  8 20:42 main.py
```
## TODOs

- [x] Think of more syntactic sugar (find a use for decorators/context
      processors?)
- [ ] Interact with background process via stdin and/or signals
- [x] Reorganize code
- [x] Tests!!! (include pypy?)
- [ ] Github actions build
- [ ] Add docstrings
- [ ] Stream and capture `stdout` and `stderr`
- [ ] Ability to source bash files
