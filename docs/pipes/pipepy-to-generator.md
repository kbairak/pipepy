# PipePy to generator

This uses Python's [passing values into a generator](https://docs.python.org/3/howto/functional.html?highlight=sending%20generator#passing-values-into-a-generator) functionality. The generator must use `a = (yield b)` syntax. The result is another generator that yields whatever the original generator yields, while the return value of each `yield` is the next non-empty line of the `PipePy` instance.

```python
from pipepy import echo

def upperize():
    line = yield
    while True:
        line = (yield line.upper())

# `upperize` is a function, `upperize()` is a generator
list(echo("aaa\nbbb") | upperize())
# <<< ["AAA\n", "BBB\n"]
```

The result is a generator, so it can be piped into another command:

```python
print(echo("aaa\nbbb") | upperize() | grep("AAA"))
# <<< AAA
```
