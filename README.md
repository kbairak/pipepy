A Python library for invoking and interacting with shell commands.

![Build](https://github.com/kbairak/pipepy/workflows/Test%20suite/badge.svg)

## Table of contents

<!--ts-->
* [Why? Comparison with other similar frameworks](#why-comparison-with-other-similar-frameworks)
* [Installation and testing](#installation-and-testing)
* [Intro, basic usage](#intro-basic-usage)
* [Customizing commands](#customizing-commands)
* [Laziness](#laziness)
   * [Background commands](#background-commands)
* [Redirecting output from/to files](#redirecting-output-fromto-files)
* [Pipes](#pipes)
* [Interacting with background processes](#interacting-with-background-processes)
* [Altering the behavior of commands](#altering-the-behavior-of-commands)
* [Miscellaneous](#miscellaneous)
* ["Interactive" mode](#interactive-mode)
* [pymake](#pymake)

<!-- Added by: kbairak, at: Tue Feb 16 09:37:02 PM EET 2021 -->

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

pymake test
# or
pytest
```

There are a few more `pymake` targets to assist with testing during
development:

- `covtest`: Produces and opens a coverage report
- `watchtest`: Listens for changes in the source code files and reruns the
  tests automatically
- `debugtest`: Runs the tests without capturing their output so that you can
  insert a debug statement

_`pymake` is a console script that is part of `pipepy` that aims to be a
replacement for GNU `make`, with the difference that the `Makefile`s are
written in Python. More on this [below](#pymake)._

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


## Laziness

Commands are evaluated lazily. For example, this will not actually do anything:

```python
from pipepy import wget
wget('http://...')
```

Invoking a `PipePy` instance with non-empty arguments will return an
**unevaluated** copy supplied with the extra arguments. A command will be
evaluated when its output is used. This can be done with the following ways:

- Accessing the `returncode`, `stdout` and `stderr` properties:

   ```python
   from pipepy import echo
   command = echo("hello world")
   command.returncode
   # <<< 0
   command.stdout
   # <<< 'hello world\n'
   command.stderr
   # <<< ''
   ```

- Evaluating the command as a string object

  ```python
  from pipepy import ls
  result = str(ls)
  # or
  print(ls)
  ```

  Converting a command to a `str` returns its `stdout`.

- Evaluating the command as a boolean object:

  ```python
  from pipepy import ls, grep
  command = ls | grep('info.txt')

  bool(command)
  # <<< True

  if command:
      print("info.txt found")
  ```

  The command will be truthy if its `returncode` is 0.

- Invoking the `.as_table()` method:

  ```python
  from pipepy import ps
  ps.as_table()
  # <<< [{'PID': '11233', 'TTY': 'pts/4', 'TIME': '00:00:01', 'CMD': 'zsh'},
  # ...  {'PID': '17673', 'TTY': 'pts/4', 'TIME': '00:00:08', 'CMD': 'ptipython'},
  # ...  {'PID': '18281', 'TTY': 'pts/4', 'TIME': '00:00:00', 'CMD': 'ps'}]
  ```

- Iterating over a command object:

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

If you are not interested in the output of a command but want to evaluate it
nevertheless, you can call it with empty arguments. So, this will actually
invoke the command (and wait for it to finish).

```python
from pipepy import wget
wget('http://...')()
```

### Background commands

Calling `.delay()` on a `PipePy` instance will return a copy that, although not
evaluated, will have started running in the background (taking inspiration from
Celery's [`.delay()`](https://docs.celeryproject.org/en/stable/reference/celery.app.task.html#celery.app.task.Task.delay)
method for the name). Again, if you try to access its output, it will perform
the rest of the evaluation process, which is simply to wait for it to finish:

```python
from pipepy import wget
urls = [...]

# All downloads will happen in the background simultaneously
downloads = [wget(url).delay() for url in urls]

# You can do something else here in Python while the downloads are working

# This will call __bool__ on all downloads and thus wait for them
if not all(downloads):
   print("Some downloads failed")
```

If you are not interested in the output of a background command, you should
take care at some point to call `.wait()` on it. Otherwise its process will not
be waited for and if the parent Python process ends, it will kill all the
background processes:

```python
from pipepy import wget
download = wget('...').delay()
# Do something else
download.wait()
```

At any point, you can call `pipepy.jobs()` to get a list of non-waited-for
commands. In case you want to do some cleaning up, there is also a
`pipepy.wait_jobs()` function. This should be used with care however as, if any
of the background jobs aren't finished or are stuck, `wait_jobs()` may hang for
an unknown amount of time.

## Redirecting output from/to files

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

If the left operand was previously evaluated, then it's output (`stdout`) will
be passed directly as input to the right operand. Otherwise, both commands will
be executed in parallel and `left`'s output will be streamed into `right`.

### 2. Left operand is any kind of iterable (including string)

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

If it's a string, it will be fed all at once

```python
result = "John is 18 years old\nMary is 25 years old" | grep("Mary")

# Equivalent to

result = ["John is 18 years old\nMary is 25 years old"] | grep("Mary")
```

In both cases, ie in all cases where the right operand is a `PipePy` object,
the return value of the pipe operation will be an **unevaluated** copy, which
will be evaluated when we try to access its output. This means that we can take
advantage of our usual background functionality:

```python
from pipepy import find, xargs
command = find('.') | xargs.wc
command = command.delay()

# Do something else in the meantime

for line in command:  # Here we wait for the command to finish
    linecount, wordcount, charcount, filename = line.split()
    # ...
```

It also means that the left operand, if it's an iterable will be consumed when
the command is evaluated.

```python
from pipepy import grep

iterable = (line for line in ["foo\n", "bar\n"])
command = iterable | grep("foo")
command.stdout
# <<< 'foo\n'
list(iterable)
# <<< []

iterable = (line for line in ["foo\n", "bar\n"])
command = iterable | grep("foo")
list(iterable)  # Lets consume the iterable prematurely
# <<< ["foo\n", "bar\n"]
command.stdout
# <<< ''
```

### 3. Right operand is a function

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

In the second case, the command and the function will be executed in parallel
and the command's `stdout` and `stderr` streams will be made available to the
function.

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
# >>> Mean time is 71.96000000000001 ms
# ... Mean time is 72.285 ms
# ... Mean time is 72.19666666666667 ms
```

If the command ends before the function, then `next(stdout)` will raise a
`StopIteration`. If the function ends before the command, the command's `stdin`
will be closed.

The return value of the pipe operation will be the return value of the
function. The function can even include the word `yield` and thus return a
generator that can be piped into another command.

Putting all of this together, we can do things like:

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

## Interacting with background processes

There are 3 ways to interact with a background process: _read-only_,
_write-only_ and _read/write_. We have already covered _read-only_ and
_write-only_:

### 1. Incrementally sending data to a command

This is done by piping from an iterable to a command. The command actually runs
in in parallel with the iterable and the iterable's data is fed to the command
as it becomes available. We will slightly modify the previous example to better
demonstrate this:

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
# <<< 0.3154888153076172 17
# ... 1.5810892581939697 17
# ... 1.7773401737213135 17
# ... 2.8303775787353516 17
# ... 3.4419643878936768 17
# ... 4.511774301528931  17
```

Here, `grep` is actually run in in parallel with the generator and matches are
printed as they are found since the command's output is being streamed to the
console, courtesy of the `_stream_stdout` argument (more on this
[below](#streaming-to-console)).

### 2. Incrementally reading data from a command

This can be done either by piping the output of a command to a function with a
subset of `stdin`, `stdout` and `stderr` as its arguments, as we demonstrated
[before](#3-right-operand-is-a-function), or by iterating over a command's
output:

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

Again, the `ping` command is actually run in parallel with the body of the
for-loop and each line is given to the body of the for-loop as it becomes
available.

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

You can call `with` on a pipe expression that involves `PipePy` objects. In
that case, each `PipePy` object's `stdout` will be connected to the next one's
`stdin`, the `stdin` offered to the body of the `with` block will be the
`stdin` of the leftmost command and the `stdout` and `stderr` offered to the
body of the `with` block will be the `stdout` and `stderr` of the rightmost
command:

```python
from pipepy import cat, grep

command = cat | grep("foo") | cat | cat | cat  # We might as well keep going
with command as (stdin, stdout, stderr):
    stdin.write("foo1\n")
    stdin.write("bar2\n")
    stdin.write("foo3\n")
    stdin.close()
    assert next(stdout).strip() == "foo1"
    assert next(stdout).strip() == "foo3"
```

## Altering the behavior of commands

### Binary mode

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
to binary mode setting its `_text` parameter to `False`:

```python
from pipepy import gzip
gzip = gzip(_text=False)
result = "hello world" | gzip
print(result.stdout)
# <<< b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\xcbH\xcd\xc9\xc9W(\xcf/\xcaI\xe1\x02\x00-;\x08\xaf\x0c\x00\x00\x00'
```

Input and output will be converted from/to binary by using the 'UTF-8'
encoding. In the previous example, our input's type was `str` and was
utf-8-encoded before being fed into `gzip`. You can change the encoding with
the `_encoding` keyword argument:

```python
from pipepy import gzip
gzip = gzip(_text=False)
result = "καλημέρα" | gzip
print(result.stdout)
# <<< b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\x01\x10\x00\xef\xff\xce\xba\xce\xb1\xce\xbb\xce\xb7\xce\xbc\xce\xad\xcf\x81\xce\xb1"\x15g\xab\x10\x00\x00\x00'
result = "καλημέρα" | gzip(_encoding="iso-8859-7")
print(result.stdout)
# <<< b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03{\xf5\xf0\xf5\xf37w?>\x04\x00\x1c\xe1\xc0\xf7\x08\x00\x00\x00'
```

### Streaming to console

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
to the user. You can force a command sto stream its whole output by setting the
`_stream` parameter:

```python
from pipepy import wget

wget('https://...', _stream=True)()
```

While `stdout` and `stderr` will not be captured, `returncode` will and thus
you can still use the command in boolean expressions:

```python
from pipepy import wget

if wget('https://...', _stream=True):
     print("Download succeeded")
else:
     print("Download failed")
```

You can call `pipepy.set_always_stream(True)` to make streaming to the console
the default behavior. This may be desirable in some situations, like Makefiles
(see [below](#pymake)).

```python
import pipepy
from pipepy import ls
pipepy.set_always_stream(True)
ls()  # Alsost equivalent to `ls(_stream=True)()`
pipepy.set_always_stream(False)
```

Similarly to how setting `_stream=True` forces a command to stream its output
to the console, setting `_stream=False` forces it to capture its output even if
`set_always_stream` has been called:

```python
import pipepy
from pipepy import ls

pipepy.set_always_stream(True)
ls()                 # Will stream its output
ls(_stream=False)()  # Will capture its output
pipepy.set_always_stream(False)
```

### Exceptions

You can call `.raise_for_returncode()` on an **evaluated** result to raise an
exception if its returncode is not 0 (think of
[requests's `.raise_for_status()`](https://requests.readthedocs.io/en/master/api/#requests.Response.raise_for_status)):

```python
from pipepy import ping, PipePyError
result = ping("asdf")()  # Remember, we have to evaluate it first

result.raise_for_returncode()
# <<< PipePyError: (2, '', 'ping: asdf: Name or service not known\n')

try:
    result.raise_for_returncode()
except PipePyError as exc:
    print(exc.returncode)
    # <<< 2
    print(exc.stdout)
    # <<< ""
    print(exc.stderr)
    # <<< ping: asdf: Name or service not known
```

You can call `pipepy.set_always_raise(True)` to have **all** commands raise an
exception if their returncode is not zero.

```python
import pipepy
from pipepy import ping
pipepy.set_always_raise(True)
ping("asdf")()
# <<< PipePyError: (2, '', 'ping: asdf: Name or service not known\n')
```

If "always raise" is set, you can still force a command to suppress its
exception by setting `_raise=False`:

```python
import pipepy
from pipepy import ping
pipepy.set_always_raise(True)
try:
    ping("asdf")()  # Will raise an exception
except Exception as exc:
    print(exc)
# <<< PipePyError: (2, '', 'ping: asdf: Name or service not known\n')

try:
    ping("asdf", _raise=False)()  # Will not raise an exception
except Exception as exc:
    print(exc)
```

## Miscellaneous

`.terminate()`, `.kill()` and `.send_signal()` simply forward the method call
to the underlying
[`Popen`](https://docs.python.org/3/library/subprocess.html#popen-objects)
object.

Here are some utilities implemented within `pipepy` that don't make use of
shell subprocesses, but we believe are useful for bash scripting.

### cd

In its simplest form, `pipepy.cd` is an alias to `os.chdir`:

```python
from pipepy import cd, pwd

print(pwd())
# <<< /foo

cd('bar')
print(pwd())
# <<< /foo/bar

cd('..')
print(pwd())
# <<< /foo
```

But it can also be used as a context processor for temporary directory changes:

```python
print(pwd())
# <<< /foo

with cd("bar"):
    print(pwd())
# <<< /foo/bar

print(pwd())
# <<< /foo
```

### export

In its simplest form, `pipepy.export` is an alias to `os.environ.update`:

```python
import os
from pipepy import export

print(os.environ['HOME'])
# <<< /home/foo

export(PATH="/home/foo/bar")
print(os.environ['HOME'])
# <<< /home/foo/bar
```

But it can also be used as a context processor for temporary environment
changes:

```python
print(os.environ['HOME'])
# <<< /home/foo

with export(PATH="/home/foo/bar"):
    print(os.environ['HOME'])
# <<< /home/foo/bar

print(os.environ['HOME'])
# <<< /home/foo
```

If an environment variable is further modified within the body of the `with`
block, it is not reverted upon exit:

```python
with export(PATH="/home/foo/bar"):
    export(PATH="/home/foo/BAR")

print(os.environ['HOME'])
# <<< /home/foo/BAR
```

## "Interactive" mode

When "interactive" mode is set, the `__repr__` method will simply return
`self.stdout + self.stderr`. This enables some very basic functionality for the
interactive python shell. To set interactive mode, run
`pipepy.set_interactive(True)`:

```python
import pipepy
from pipepy import ls, overload_chars
pipepy.set_interactive(True)
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

## pymake

Bundled with this library there is a command called `pymake` which aims to
replicate the syntax and behavior of GNU `make` as much as possible, but in
Python. A `Makefile.py` file looks like this (this is actually part of the
Makefile of the current library):

```python
import pipepy
from pipepy import python, rm

pipepy.set_always_stream(True)
pipepy.set_always_raise(True)

def clean():
    rm('-rf', "build", "dist")()

def build(clean):
    python('-m', "build")()

def publish(build):
    python('-m', "twine").upload("dist/*")()
```

You can now run `pymake publish` to run the `publish` make target, along with
its dependencies. The names of the functions' arguments are used to define the
dependencies, so `clean` is a dependency of `build` and `build` is a dependency
of `publish`.

_(You don't have to use `pipepy` commands inside `Makefile.py`, but admittedly
it's a very good fit)_

The arguments hold any return values of the dependency targets:

```python
def a():
    return 1

def b():
    return 2

def c(a, b):
    print(a + b)
```

```sh
→ pymake c
# ← 3
```

Each dependency will be executed at most once, even if it's used as a
dependency more than once:

```python
def a():
    print("pymake target a")

def b(a):
    print("pymake target b")

def c(a, b):
    print("pymake target c")
```

```sh
→ pymake c
# ← pymake target a
# ← pymake target b
# ← pymake target c
```

You can set the `DEFAULT_PYMAKE_TARGET` global variable to define the default
target.

```python
from pipepy import pytest

DEFAULT_PYMAKE_TARGET = "test"

def test():
    pytest(_stream=True)()
```

### `pymake` variables

Apart from dependencies, you can use function arguments to define variables
that can be overridden by the invocation of `pymake`. This can be done in 2
ways:

1. Using the function's keyword arguments:

   ```python
   # Makefile.py

   def greeting(msg="world"):
       print(f"hello {msg}")
   ```

   ```sh
   → pymake greeting
   # ← hello world
   
   → pymake greeting msg=Bill
   # ← hello Bill
   ```

2. Using global variables defined in `Makefile.py`:

   ```python
   # Makefile.py

   msg = "world"

   def greeting(msg):
       print(f"hello {msg}")
   ```

   ```sh
   → pymake greeting
   # ← hello world
   
   → pymake greeting msg=Bill
   # ← hello Bill
   ```

### Shell completion for `pymake`

If you want to enable shell completion for `pymake` targets you should run:

```sh
complete -C _pymake_complete pymake
```

in bash or 

```sh
complete -F _pymake_complete pymake
```

in zsh.

_(`_pymake_complete` is an executable installed with `pipepy` for this
purpose)_


## TODOs

- [x] Context processors for `cd` and/or environment
- [x] `jobs` implementation
- [ ] Ability to source bash files
- [ ] Python virtual environments (maybe sourcing bash files will suffice)
- [x] Autocomplete for `pymake`
