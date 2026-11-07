# pipepy

A Python library for invoking and interacting with shell commands.

`pipepy` is a library to help writing python scripts that look, and work, like shell scripts.
Interact with operating system commands as if they were simply python functions. Have
interoperability between the shell and python parts of the scripts.

The code is pure Python, but with a lot of syntax tricks that should feel familiar to shell
scripters. At its heart, `pipepy` is a wrapper around the `subprocess` module.

## Basic usage

```python
from pipepy import ls, grep

print(ls)  # prints contents of current folder
if ls | grep('info.txt'):
      print('info.txt found')
```

## Importing commands

Most shell commands are importable straight from the `pipepy` module. Dashes in commands' names are
converted to underscore (`docker-compose` → `docker_compose`).

```python
from pipepy import ls, grep, docker_compose
```

Commands that cannot be found automatically can be created with the `PipePy` constructor:

```python
from pipepy import PipePy

custom_command = PipePy('./bin/custom')
python_script = PipePy('python', 'script.py')
```

[![Build](https://github.com/kbairak/pipepy/workflows/Test%20suite/badge.svg)](https://github.com/kbairak/pipepy/actions)

## Why? Comparison with other similar frameworks

1. **[Xonsh](https://xon.sh/)**: Xonsh allows you to combine shell and Python and enables very
   powerful scripting and interactive sessions. This library does the same to a limited degree.
   However, Xonsh introduces a new language that is a superset of Python. The main goal of this
   library that sets it apart is that it is intended to be a pure Python implementation, mainly
   aimed at scripting.

2. **[sh](https://github.com/amoffat/sh)** and **[pieshell](https://github.com/redhog/pieshell)**:
   These are much closer to the current library in that they are pure Python implementations. The
   current library, however, tries to improve on the following aspects:

   - It tries to apply more syntactic sugar to make the invocations feel more like shell
     invocations.

   - It tries to offer ways to have shell commands interact with python code in powerful and
     intuitive ways.
