import os
import pathlib
import re
import stat as stat_  # aliasing because there's a 'stat' UNIX command
import string

from .pipepy import PipePy


def overload_chars(locals_):
    """ Assigns all ascii characters as values to keys of the same name in the
        `locals_` argument. Intended to overload the `locals()` call of modules
        that import `pipepy`

            >>> from pipepy import overload_chars, ls
            >>> overload_chars(locals())
            >>> ls -l
            <<< -rw-r--r-- 1 kbairak kbairak 9401 Feb  3 23:12 foo.txt
            ... -rw-r--r-- 1 kbairak kbairak 8923 Feb  3 23:06 bar.txt
    """

    for char in string.ascii_letters:
        if char in locals_:
            continue
        locals_[char] = char


for path in os.get_exec_path():
    try:
        listdir = os.listdir(path)
    except FileNotFoundError:
        continue
    for original_name in listdir:
        name = original_name.replace('-', '_')
        if name in locals():
            continue
        if 'x' in stat_.filemode(
                os.lstat(os.path.join(path, original_name)).st_mode):
            locals()[name] = PipePy(original_name)


class cd:
    """ `cd` replacement that can be also used as a context processor.

        Equivalent to `os.chdir`:

            >>> from pipepy import cd, pwd

            >>> print(pwd())
            <<< /foo

            >>> cd('bar')
            >>> print(pwd())
            <<< /foo/bar

            >>> cd('..')
            >>> print(pwd())
            <<< /foo

        Usage as context processor

            >>> from pipepy import cd, pwd

            >>> print(pwd())
            <<< /foo

            >>> with cd('bar'):
            ...     print(pwd())
            <<< /foo/bar

            >>> print(pwd())
            <<< /foo
    """

    def __init__(self, *args, **kwargs):
        self._previous_dir = os.path.abspath(os.curdir)
        os.chdir(*args, **kwargs)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self._previous_dir)


class export:
    """ `export` replacement that can also be used as a context processor.

        Equivalent to `export`:

            >>> import os
            >>> from pipepy import export

            >>> print(os.environ['PATH'])
            <<< foo

            >>> export(PATH="foo:bar")
            >>> print(os.environ['PATH'])
            <<< foo:bar

            >>> export(PATH="foo")
            >>> print(os.environ['PATH'])
            <<< foo

        Usage as a context processor:

            >>> import os
            >>> from pipepy import export

            >>> print(os.environ['PATH'])
            <<< foo

            >>> with export(PATH="foo:bar"):
            ...     print(os.environ['PATH'])
            <<< foo:bar

            >>> print(os.environ['PATH'])
            <<< foo

        If an env variable is further changed within the body of `with`, it is
        not restored.

            >>> with export(PATH="foo:bar"):
            ...     export(PATH="foo:BAR")
            >>> print(os.environ['PATH'])
            <<< foo:BAR
    """

    def __init__(self, **kwargs):
        self._previous_env = dict(os.environ)
        self._kwargs = kwargs

        os.environ.update(kwargs)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        for key, value in self._kwargs.items():
            if os.environ[key] != value:
                # Variable changed within the body of the `with` block, skip
                pass
            elif key in self._previous_env:
                # Value was changed by the `with` statement, restore
                os.environ[key] = self._previous_env[key]
            else:
                # Value was added by the `with` statement, delete
                del os.environ[key]


def source(filename, *, recursive=False, quiet=True, shell="bash"):
    """ Source a bash script and export any environment variables defined
        there.

        - filename: The name of the file being sourced, defaults to 'env'
        - recursive: Whether to go through all the parent directories to find
              similarly named bash scripts, defaults to `False`
        - shell: which shell to use for sourcing, defaults to 'bash'

        Can also be used as a context processor for temporary environment
        changes, like `export` (in fact, it uses `export` internally).

        Usage:

        Assuming our directory structure is:

            - a/
              - env (export AAA="aaa")
              - b/
                - env (export BBB="bbb")

        and our current directory is `a/b`:

            >>> 'BBB' in os.environ
            <<< False

            >>>  with source('env'):
            ...     os.environ['BBB']
            <<< 'bbb'

            >>> 'BBB' in os.environ
            <<< False

            >>> source('env')
            >>> os.environ['BBB']
            <<< 'bbb'

            >>>  with source('env', recursive=True):
            ...     os.environ['AAA']
            <<< 'aaa'

            >>> 'AAA' in os.environ
            <<< False

            >>> source('env', recursive=True)
            >>> os.environ['AAA']
            <<< 'aa'
    """

    ptr = pathlib.Path('.').resolve()
    filenames = []
    if (ptr / filename).exists() and (ptr / filename).is_file():
        filenames.append(str((ptr / filename).resolve()))
    if recursive:
        while True:
            ptr = ptr.parent
            if (ptr / filename).exists() and (ptr / filename).is_file():
                filenames.append(str((ptr / filename).resolve()))
            if ptr == ptr.parent:
                break

    env = {}
    shell_cmd = globals()[shell]
    for filename in reversed(filenames):
        result = f"source {filename} && declare -x" | shell_cmd
        if not result:
            if quiet:
                continue
            else:
                result.raise_for_returncode()
        for line in result:
            match = re.search(r'^declare -x ([^=]+)="(.*)"$', line.strip())
            if not match:
                continue
            key, value = match.groups()
            if key not in os.environ or value != os.environ[key]:
                env[key] = value
    return export(**env)
