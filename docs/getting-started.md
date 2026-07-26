# Getting started

## Basic usage

```python
from pipepy import ls, grep

print(ls)  # prints contents of current folder
if ls | grep('info.txt'):
      print('info.txt found')
```

## Importing commands

Most shell commands are importable straight from the `pipepy` module. Dashes in commands' names are converted to underscore (`docker-compose` → `docker_compose`).

```python
from pipepy import ls, grep, docker_compose
```

Commands that cannot be found automatically can be created with the `PipePy` constructor:

```python
from pipepy import PipePy

custom_command = PipePy('./bin/custom')
python_script = PipePy('python', 'script.py')
```
