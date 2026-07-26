# Altering the behavior of commands

## Binary mode

All commands execute in text mode by default (dealing with `str` objects). This can cause problems with binary data.

```python
from pipepy import gzip
result = "hello world" | gzip
print(result.stdout)
# <<< UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8b
```

Set `_text=False` for binary mode:

```python
from pipepy import gzip
gzip = gzip(_text=False)
result = "hello world" | gzip
print(result.stdout)
# <<< b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03...'
```

Change encoding with the `_encoding` keyword argument:

```python
from pipepy import gzip
gzip = gzip(_text=False)
result = "καλημέρα" | gzip
result = "καλημέρα" | gzip(_encoding="iso-8859-7")
```

## Streaming to console

Set `_stream_stdout=True` or `_stream_stderr=True` to stream those streams to the console instead of capturing them. Useful for interactive commands like `fzf`:

```python
from pipepy import fzf
fzf = fzf(_stream_stderr=True)

print("John\nMary" | fzf)
# <<< Mary
```

Or `dialog`:

```python
from pipepy import dialog
dialog = dialog(_stream_stdout=True)

result = dialog(checklist=True)('Choose name', 30, 110, 0,
                                "John", '', "on",
                                "Mary", '', "off")
print(result.stderr)
# <<< John
```

Force full streaming with `_stream`:

```python
from pipepy import wget
wget('https://...', _stream=True)()
```

`returncode` is still available, so you can use the command in boolean expressions:

```python
from pipepy import wget
if wget('https://...', _stream=True):
     print("Download succeeded")
else:
     print("Download failed")
```

### Global streaming mode

Call `pipepy.set_always_stream(True)` to make streaming the default:

```python
import pipepy
from pipepy import ls
pipepy.set_always_stream(True)
ls()  # Equivalent to `ls(_stream=True)()`
pipepy.set_always_stream(False)
```

Override with `_stream=False`:

```python
import pipepy
from pipepy import ls

pipepy.set_always_stream(True)
ls()                 # Will stream
ls(_stream=False)()  # Will capture
pipepy.set_always_stream(False)
```

## Exceptions

Call `.raise_for_returncode()` on an **evaluated** result to raise an exception if returncode is not 0.

```python
from pipepy import ping, PipePyError
result = ping("asdf")()  # Evaluate first

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

### Global raise mode

Set `pipepy.set_always_raise(True)` to have all commands raise on non-zero returncode:

```python
import pipepy
from pipepy import ping
pipepy.set_always_raise(True)
ping("asdf")()
# <<< PipePyError: (2, '', 'ping: asdf: Name or service not known\n')
```

Override per-command with `_raise=False`:

```python
import pipepy
from pipepy import ping
pipepy.set_always_raise(True)
ping("asdf", _raise=False)()  # Will not raise
```

## Interactive mode

When "interactive" mode is set, `__repr__` returns `self.stdout + self.stderr`. Useful for interactive Python shells.

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
# ... -rw-r--r-- 1 kbairak kbairak ...
```

## Making alterations "permanent"

Create `PipePy` instances with alterations and use them as templates:

```python
stream_sh = PipePy(_stream=True)
stream_sh
# <<< PipePy()
stream_sh._stream
# <<< True

stream_sh.ls
# <<< PipePy('ls')
stream_sh.ls._stream
# <<< True

r = stream_sh.ls()
# output is streamed to console
r.stdout
# <<< None
r.returncode
# <<< 0
```

```python
raise_sh = PipePy(_raise=True)
raise_sh.false
# <<< PipePy('false')
raise_sh.false()
# <<< PipePyError: (1, '', '')
```

This is a more contained alternative to `set_always_stream` and `set_always_raise`.

## Process control

`.terminate()`, `.kill()` and `.send_signal()` forward to the underlying `Popen` object.

```python
from pipepy import sleep
cmd = sleep(100).delay()
cmd.terminate()
# or
cmd.kill()
# or
cmd.send_signal(signal.SIGTERM)
```
