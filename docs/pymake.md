# pymake

Bundled with this library is a command called `pymake` which replicates the syntax and behavior of GNU `make`, but in Python.

## Makefile.py example

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

Run `pymake publish` to run the `publish` target along with its dependencies. Function argument names define dependencies, so `clean` is a dependency of `build` and `build` is a dependency of `publish`.

_(You don't have to use `pipepy` commands inside `Makefile.py`, but it's a very good fit.)_

## Return values

Arguments hold the return values of dependency targets:

```python
def a():
    return 1

def b():
    return 2

def c(a, b):
    print(a + b)
```

```sh
pymake c
# ← 3
```

## Single execution

Each dependency executes at most once, even if used multiple times:

```python
def a():
    print("pymake target a")

def b(a):
    print("pymake target b")

def c(a, b):
    print("pymake target c")
```

```sh
pymake c
# ← pymake target a
# ← pymake target b
# ← pymake target c
```

## Default target

Set `DEFAULT_PYMAKE_TARGET` to define the default target:

```python
from pipepy import pytest

DEFAULT_PYMAKE_TARGET = "test"

def test():
    pytest(_stream=True)()
```

```sh
pymake  # runs the 'test' target
```

## Variables

Apart from dependencies, function arguments can define variables overridden by the invocation:

### Via function keyword arguments

```python
# Makefile.py
def greeting(msg="world"):
    print(f"hello {msg}")
```

```sh
pymake greeting
# ← hello world

pymake greeting msg=Bill
# ← hello Bill
```

### Via global variables

```python
# Makefile.py
msg = "world"

def greeting():
    print(f"hello {msg}")
```

```sh
pymake greeting
# ← hello world

pymake greeting msg=Bill
# ← hello Bill
```

## Shell completion

`pymake` supports shell completion for bash and zsh.

### Bash

```sh
eval $(pymake --setup-bash-completion)
```

```
$ pymake <TAB><TAB>
build      clean      debugtest  publish    watchtest
checks     covtest    html       test
```

### Zsh

```sh
eval $(pymake --setup-zsh-completion)
```

```
$ pymake <TAB>
build      -- Build package
checks     -- Run static checks on the code (flake8, isort)
clean      -- Clean up build directories
...
```

Descriptions are taken from the `pymake` targets' docstrings.

Put the `eval` statements in your `.bashrc`/`.zshrc`.
