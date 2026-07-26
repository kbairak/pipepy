# Laziness

Commands are evaluated lazily. This will not actually do anything:

```python
from pipepy import wget
wget('http://...')
```

Invoking a `PipePy` instance with non-empty arguments returns an **unevaluated** copy supplied with extra arguments. A command is evaluated when its output is used.

## Accessing returncode, stdout, stderr

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

## Evaluating as string

```python
from pipepy import ls
result = str(ls)
# or
print(ls)
```

Converting a command to `str` returns its `stdout`.

## Evaluating as boolean

```python
from pipepy import ls, grep
command = ls | grep('info.txt')

bool(command)
# <<< True

if command:
    print("info.txt found")
```

The command is truthy if its `returncode` is 0.

## .as_table()

```python
from pipepy import ps
ps.as_table()
# <<< [{'PID': '11233', 'TTY': 'pts/4', 'TIME': '00:00:01', 'CMD': 'zsh'},
# ...  {'PID': '17673', 'TTY': 'pts/4', 'TIME': '00:00:08', 'CMD': 'ptipython'},
# ...  {'PID': '18281', 'TTY': 'pts/4', 'TIME': '00:00:00', 'CMD': 'ps'}]
```

## Iterating over output

```python
from pipepy import ls
for filename in ls:
    print(filename.upper())
```

## iter_words()

```python
from pipepy import ps
list(ps.iter_words())
# <<< ['PID', 'TTY', 'TIME', 'CMD',
# ...  '11439', 'pts/5', '00:00:00', 'zsh',
# ...  '15532', 'pts/5', '00:00:10', 'ptipython',
# ...  '15539', 'pts/5', '00:00:00', 'ps']
```

## Evaluation via redirection

`ls \| grep('info.txt')` evaluates `ls` and streams its output into `grep`.

```python
from pipepy import ls, grep
ls > 'files.txt'
ls >> 'files.txt'
ls | grep('info.txt')
ls | lambda output: output.upper()
```

## Forcing evaluation

If you are not interested in the output but want to evaluate a command, call it with empty arguments.

```python
from pipepy import wget
wget('http://...')()
```
