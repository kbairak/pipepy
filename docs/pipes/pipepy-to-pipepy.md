# PipePy to PipePy

If both operands are `PipePy` instances, the result is as close as possible to a shell pipe.

```python
from pipepy import git, grep
if git.diff(name_only=True) | grep('readme.txt'):
      print("readme was changed")
```

If the left operand was previously evaluated, its `stdout` is passed directly as input to the right operand. Otherwise, both commands execute in parallel and the left's output is streamed into the right.
