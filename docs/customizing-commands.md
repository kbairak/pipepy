# Customizing commands

Calling a command with non-empty arguments will return a modified unevaluated copy.

```python
from pipepy import PipePy
ls_l = PipePy('ls', '-l')
# Is equivalent to
ls_l = PipePy('ls')('-l')
```

## Globs

Globbing will be applied to all positional arguments.

```python
from pipepy import echo
print(echo('*'))  # Will print all files in the current folder
```

Use `glob.escape` to avoid globbing:

```python
import glob
from pipepy import ls, echo

print(ls)
# <<< **a *a *aa

print(echo('*a'))
# <<< **a *a *aa

print(echo(glob.escape('*a')))
# <<< *a
```

## Keyword arguments

```python
from pipepy import ls
ls(sort="size")     # Equivalent to ls('--sort=size')
ls(I="files.txt")   # Equivalent to ls('-I', 'files.txt')
ls(sort_by="size")  # Equivalent to ls('--sort-by=size')
ls(escape=True)     # Equivalent to ls('--escape')
ls(escape=False)    # Equivalent to ls('--no-escape')
```

Since keyword arguments come after positional arguments, if you want the final command to have a different ordering you can invoke the command multiple times:

```python
from pipepy import ls
ls('-l', sort="size")  # Equivalent to ls('-l', '--sort=size')
ls(sort="size")('-l')  # Equivalent to ls('--sort=size', '-l')
```

## Attribute access

```python
from pipepy import git
git.push.origin.bugfixes  # Equivalent to git('push', 'origin', 'bugfixes')
```

## Minus sign

```python
from pipepy import ls
ls - 'l'        # Equivalent to ls('-l')
ls - 'default'  # Equivalent to ls('--default')
```

This enables making invocations look more like the shell:

```python
from pipepy import ls
l, t = 'l', 't'
ls -l -t  # Equivalent to ls('-l', '-t')
```

Call `pipepy.overload_chars(locals())` to assign all ascii letters to variables of the same name:

```python
import pipepy
from pipepy import ls
pipepy.overload_chars(locals())
ls -l -t  # Equivalent to ls('-l', '-t')
```
