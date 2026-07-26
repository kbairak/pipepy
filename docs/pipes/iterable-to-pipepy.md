# Iterable to PipePy

If the left operand is any kind of iterable, its elements are fed to the command's stdin.

```python
from pipepy import grep

result = ["John is 18 years old\n", "Mary is 25 years old"] | grep("Mary")
print(result)
# <<< Mary is 25 years old
```

## Generator as input

```python
import random
from pipepy import grep

def my_stdin():
    for _ in range(500):
        yield f"{random.randint(1, 100)}\n"

result = my_stdin() | grep(17)
print(result)
```

## String as input

If it's a string, it's fed all at once:

```python
result = "John is 18 years old\nMary is 25 years old" | grep("Mary")
```

## Background with pipes

The return value is an **unevaluated** copy, so you can use background functionality:

```python
from pipepy import find, xargs
command = find('.') | xargs.wc
command = command.delay()

# Do something else

for line in command:
    linecount, wordcount, charcount, filename = line.split()
    # ...
```

## Input consumption

The left operand iterable is consumed when the command is evaluated.

```python
from pipepy import grep

iterable = (line for line in ["foo\n", "bar\n"])
command = iterable | grep("foo")
command.stdout
# <<< 'foo\n'
list(iterable)
# <<< []
```

## Function-call style

If you prefer a function-call style over a shell pipe operation, use the `_input` keyword argument:

```python
from pipepy import grep, ls

grep('setup', _input=ls)
# Is equivalent to
ls | grep('setup')
```

Or use the square-bracket notation:

```python
from pipepy import grep, ls

grep('setup')[ls]
# Is equivalent to
ls | grep('setup')
```

_(We use parentheses for arguments and square brackets for input because parentheses let us use keyword arguments which are a good fit for command-line options.)_
