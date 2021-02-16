import os
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
                # Env variable changed within the body of the block, skip
                pass
            elif key in self._previous_env:
                # Value was changed by the `with` statement, restore
                os.environ[key] = self._previous_env[key]
            else:
                # Value was added by the `with` statement, delete
                del os.environ[key]
