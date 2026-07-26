# Redirecting output from/to files

The `>`, `>>` and `<` operators work similar to how they work in a shell.

```python
from pipepy import ls, grep

ls               >  'files.txt'  # Will overwrite files.txt
ls               >> 'files.txt'  # Will append to files.txt
grep('info.txt') <  'files.txt'  # Will use files.txt as input
```

## File-like objects

These also work with file-like objects:

```python
import io
from pipepy import ls, grep

buf = io.StringIO()
ls > buf
ls('subfolder') >> buf

buf.seek(0)
grep('filename') < buf
```

## Combining redirects

If you want to combine input and output redirections, put the first redirection inside parentheses due to Python's comparison chaining:

```python
from pipepy import gzip
gzip = gzip(_text=False)
gzip < 'uncompressed.txt' > 'uncompressed.txt.gz'    # Wrong!
(gzip < 'uncompressed.txt') > 'uncompressed.txt.gz'  # Correct!
```
