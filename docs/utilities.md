# Utilities

These utilities are implemented within `pipepy` and don't make use of shell subprocesses, but are useful for scripting.

## cd

`pipepy.cd` is an alias to `os.chdir`:

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

It can also be used as a context manager for temporary directory changes:

```python
print(pwd())
# <<< /foo

with cd("bar"):
    print(pwd())
# <<< /foo/bar

print(pwd())
# <<< /foo
```

## export

`pipepy.export` is an alias to `os.environ.update`:

```python
import os
from pipepy import export

print(os.environ['HOME'])
# <<< /home/foo

export(PATH="/home/foo/bar")
print(os.environ['HOME'])
# <<< /home/foo/bar
```

It can also be used as a context manager:

```python
print(os.environ['HOME'])
# <<< /home/foo

with export(PATH="/home/foo/bar"):
    print(os.environ['HOME'])
# <<< /home/foo/bar

print(os.environ['HOME'])
# <<< /home/foo
```

If an environment variable is further modified inside the `with` block, it is not reverted upon exit:

```python
with export(PATH="/home/foo/bar"):
    export(PATH="/home/foo/BAR")

print(os.environ['HOME'])
# <<< /home/foo/BAR
```

## source

The `source` function runs a bash script, extracts resulting environment variables, and saves them on the current environment. It can be used as a context manager.

```bash
# env
export AAA=aaa
```

```python
import os
from pipepy import source

with source('env'):
    print(os.environ['AAA'])
# <<< aaa
'AAA' in os.environ
# <<< False

source('env')
print(os.environ['AAA'])
# <<< aaa
```

### Recursive sourcing

If `recursive=True`, all files with the same name in the current directory and all parents will be sourced, in reverse order.

```
- /home/kbairak/env:
    export COMPOSE_PROJECT_NAME="pipepy"
- /home/kbairak/project/env:
    export COMPOSE_FILE="docker-compose.yml:docker-compose-dev.yml"
```

```python
from pipepy import cd, source, docker_compose
cd('/home/kbairak/project')
source('env', recursive=True)
```

### Keyword arguments

- **recursive** (boolean, defaults to `False`): Source all files with the same name from current directory up to root.
- **quiet** (boolean, defaults to `True`): If the sourced file fails, skip without complaint.
- **shell** (string, defaults to `'bash'`): The shell command used for sourcing.
