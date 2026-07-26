# Chaining pipes

Putting everything together, you can chain multiple operations in a single pipeline.

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

The pipeline flows as follows:
1. Generator `my_input()` yields lines
2. `cat` passes them through
3. `grep('line')` filters to matching lines
4. `my_output` transforms each line to uppercase (as a generator)
5. `grep("TWO")` filters again
