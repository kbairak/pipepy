import reprlib
import inspect
import subprocess
from glob import glob

INTERACTIVE = False


def set_interactive(value):
    global INTERACTIVE
    INTERACTIVE = value


class PipePy:
    """ Convenience utility for invoking shell commands.

        Usage:

            >>> igrep = PipePy('grep', '-i')
            >>> ls = PipePy('ls')
            >>> ps = PipePy('ps')

            >>> result = ls('-l') | igrep('main')
            >>> result.stdout
            <<< '-rw-r--r-- 1 kbairak kbairak 3163 Jan 22 09:11 main.py'
            >>> result.returncode
            <<< 0
            >>> bool(result)
            <<< True
    """

    class _NONE:
        pass

    def __init__(self, *args, _lazy=False, _stdin=None, _stream_stdout=False,
                 _stream_stderr=False, _wait=True, _text=True,
                 _encoding="utf8", **kwargs):
        """ Initialize a PipePy object.

            `args` and `kwargs` will determine the command line arguments
            passed to the subprocess. The rest of the keyword arguments
            customize how the subprocess will be executed. See `_evaluate`'s
            docstring for details.

            Generally the keyword arguments should not be set by hand but by
            other methods of PipePy, with the exception of `_stream_stdout`,
            `_stream_stderr` and `_encoding` for which no fancy syntax exists
            (yet).
        """

        self._args = self._convert_args(args, kwargs)
        self._lazy = _lazy
        self._stdin = _stdin
        self._stream_stdout = _stream_stdout
        self._stream_stderr = _stream_stderr
        self._wait = _wait
        self._text = _text
        self._encoding = _encoding
        self._stdin_close_pending = False
        self._context = None  # To be used with `with` statements

        self._returncode = None
        self._stdout = None
        self._stderr = None

    # Customizing instance
    def __call__(self, *args, _stdin=_NONE, _stream_stdout=_NONE,
                 _stream_stderr=_NONE, _wait=_NONE, _text=_NONE,
                 _encoding=_NONE, **kwargs):
        """ Make and return a copy of `self` overriding some of it's
            initialization arguments. Also, if `__call__` is called with no
            arguments, an evaluation will be forced on the returned copy.

            The copy will not be lazy (see `_evaluate`'s docstring).

                >>> ls_l = PipePy('ls', '-l')

            is *almost* equivalent to

                >>> ls = PipePy('ls')
                >>> ls_l = ls('-l')
        """

        force = (not args and
                 not kwargs and
                 _stdin is self._NONE and
                 _stream_stdout is self._NONE and
                 _stream_stderr is self._NONE and
                 _wait is self._NONE and
                 _text is self._NONE and
                 _encoding is self._NONE)

        args = self._args + list(args)

        if _stdin is self._NONE:
            _stdin = self._stdin
        if _stream_stdout is self._NONE:
            _stream_stdout = self._stream_stdout
        if _stream_stderr is self._NONE:
            _stream_stderr = self._stream_stderr
        if _wait is self._NONE:
            _wait = self._wait
        if _text is self._NONE:
            _text = self._text
        if _encoding is self._NONE:
            _encoding = self._encoding

        result = self.__class__(*args,
                                _lazy=True,
                                _stdin=_stdin,
                                _stream_stdout=_stream_stdout,
                                _stream_stderr=_stream_stderr,
                                _wait=_wait,
                                _text=_text,
                                _encoding=_encoding,
                                **kwargs)

        if force:
            result._evaluate()

        return result

    def __sub__(left, right):
        """ Alternate method of adding switches to commands:

                >>> ls - 'l'
                >>> # is equivalent to
                >>> ls('-l')

            If the right operand is longer than 1 character, 2 dashes will be
            used:

                >>> ls - 'escape'
                >>> # is equivalent to
                >>> ls('--escape')
        """

        if len(right) == 1:
            return left(f"-{right}")
        else:
            return left(f"--{right}")

    def __getattr__(self, attr):
        """ Alternate way of pasing arguments to commands. Essentially

                >>> git = PipePy('git')
                >>> git.status

            should be equivalent to

                >>> git('status')
        """

        return self.__class__(*(self._args + [attr]), _lazy=False)

    def __invert__(self):
        """ Set binary mode:

            Usage:

                >>> (ls | ~gzip)()
        """

        return self(_text=False)

    def __neg__(self):
        return self(_wait=False)()

    def __pos__(self):
        return self(_stream_stdout=True, _stream_stderr=True)

    @staticmethod
    def _convert_args(args, kwargs):
        """ Do some fancy processing of arguments. The intention is to enable
            things like:

                >>> PipePy('sleep', 10)
                >>> # Equivalent to
                >>> PipePy('sleep', '10')

                >>> PipePy('ls', sort="size")
                >>> # Equivalent to
                >>> PipePy('ls', '--sort=size')

                >>> PipePy('ls', escape=True)
                >>> # Equivalent to
                >>> PipePy('ls', '--escape')

            Because positional arguments come before keyword arguments and the
            order of keyword arguments is not guaranteed, you can apply
            multiple function calls to enforce your preferred ordering:

                >>> PipePy('ls', sort="size")('-l')
                >>> # Equivalent to
                >>> PipePy('ls', '--sort=size', '-l')
        """

        args = [str(arg) for arg in args]

        final_args = []
        for arg in args:
            arg = str(arg)
            globbed = glob(arg, recursive=True)
            if globbed:
                final_args.extend(globbed)
            else:
                final_args.append(arg)

        for key, value in kwargs.items():
            key = key.replace('_', '-')
            if value is True:
                final_args.append(f"--{key}")
            elif value is False:
                final_args.append(f"--no-{key}")
            else:
                final_args.append(f"--{key}={value}")
        return final_args

    # Evaluation
    def _evaluate(self):
        """ Actually evaluates the subprocess. `__init__`'s keyword arguments
            change how this behaves:

            - _lazy: If True and this instance has been evaluated before, it
                  will do nothing. Otherwise a new evaluation will be forced.

            - _stdin: If set, it will be passed to the subprocess as its
                  standard input. If it's a file-like object, it will be
                  directly set as the subprocess's stdin, otherwise it will be
                  passed to a `Popen.communicate` call later on

            - _stream_stdout: If true, `None` will be set as the subprocess's
                  stdout, resulting in its output being streamed to the console
                  and thus not captured by `self._stdout`

            - _stream_stderr: Same as `_stream_stdout`, but for stderr

            - _text: Whether the subprocess will be opened in text mode.
                  Defaults to True

            - _wait: Whether the subprocess will be waited for. If False, the
                  caller may interact with the process via `self._process`,
                  before waiting for it with `self.wait()`
        """

        if self._returncode is not None and self._lazy:
            return

        if self._stdin is not None:
            if self._stdin is not None and hasattr(self._stdin, 'read'):
                # File-like object
                stdin = self._stdin
            else:
                stdin = subprocess.PIPE
        elif not self._wait:
            stdin = subprocess.PIPE
        else:
            stdin = None

        if self._stream_stdout:
            stdout = None
        else:
            stdout = subprocess.PIPE

        if self._stream_stderr:
            stderr = None
        else:
            stderr = subprocess.PIPE

        self._process = subprocess.Popen(self._args, stdin=stdin,
                                         stdout=stdout, stderr=stderr,
                                         text=self._text)

        if self._wait:
            self.wait()

    def wait(self):
        if isinstance(self._stdin, (bytes, str)):
            stdin = self._stdin
        else:
            stdin = None
        self._stdout, self._stderr = self._process.communicate(stdin)
        self._returncode = self._process.wait()

    # Get results
    @property
    def returncode(self):
        """ Lazily return the subprocess's return code. """

        self._evaluate()
        return self._returncode

    @property
    def stdout(self):
        """ Lazily return the subprocess's stdout. """

        self._evaluate()
        return self._stdout

    @property
    def stderr(self):
        """ Lazily return the subprocess's stderr. """

        self._evaluate()
        return self._stderr

    def __bool__(self):
        """ Use in boolean expressions.

            Usage:

                >>> git = PipePy('git')
                >>> grep = PipePy('grep')

                >>> if git('branch') | grep('my_feature'):
                ...     print("Branch found")
        """

        return self.returncode == 0

    def __str__(self):
        """ Return stdout as string, even if the subprocess is opened in binary
            mode. """
        result = self.stdout
        if not self._text:
            result = result.decode(self._encoding)
        return result

    def as_table(self):
        """ Usage:

            >>> ps = PipePy('ps')
            >>> ps.as_table()
            <<< [{'PID': '11233', 'TTY': 'pts/4', 'TIME': '00:00:01',
            ...   'CMD': 'zsh'},
            ...  {'PID': '17673', 'TTY': 'pts/4', 'TIME': '00:00:08',
            ...   'CMD': 'ptipython'},
            ...  {'PID': '18281', 'TTY': 'pts/4', 'TIME': '00:00:00',
            ...   'CMD': 'ps'}]
        """
        lines = self.stdout.splitlines()
        fields = lines[0].split()
        result = []
        for line in lines[1:]:
            item = {}
            for i, value in enumerate(line.split(maxsplit=len(fields) - 1)):
                item[fields[i]] = value
            result.append(item)
        return result

    def __iter__(self):
        """ Support the iteration interface:

            Usage:

                >>> ls = PipePy('ls')
                >>> for name in ls:
                ...     print(ls.upper())
        """

        if self._stdout is not None:
            yield from str(self).splitlines()
        else:
            command = -self
            for line in command._process.stdout:
                yield line

    def iter_words(self):
        for line in self:
            yield from iter(line.split())

    def __repr__(self):
        if INTERACTIVE:
            return self._interactive_repr()
        else:
            return self._normal_repr()

    def _normal_repr(self):
        result = ["PipePy("]
        if self._args:
            result.append(', '.join((repr(arg) for arg in self._args)))
        else:
            result.append('[]')
        if self._stdin is not None:
            result.extend([", _stdin=", reprlib.repr(self._stdin)])
        if self._returncode is not None:
            result.extend([", returncode=", reprlib.repr(self._returncode)])
            if self._stdout is not None:
                result.extend([", stdout=", reprlib.repr(self._stdout)])
            if self._stderr:
                result.extend([", stderr=", reprlib.repr(self._stderr)])
        result.append(')')
        return ''.join(result)

    def _interactive_repr(self):
        self._evaluate()
        result = self.stdout + self.stderr
        if not self._text:
            result = result.decode(self._encoding)
        return result

    # Redirect output
    def __gt__(self, filename):
        """ Write output to file

            Usage:

                >>> ps = PipePy('ps')
                >>> ps > 'progs.txt'
        """

        if self._text:
            mode = "w"
        else:
            mode = "wb"

        with open(filename, mode, encoding=self._encoding) as f:
            f.write(self.stdout)

    def __rshift__(self, filename):
        """ Append output to file

            Usage:

                >>> ps = PipePy('ps')
                >>> ps >> 'progs/txt'
        """

        if self._text:
            mode = "a"
        else:
            mode = "ab"

        with open(filename, mode, encoding=self._encoding) as f:
            f.write(self.stdout)

    def __lt__(self, filename):
        """ Use file as input

            Usage:

                >>> grep = PipePy('grep')
                >>> grep('python') < 'progs.txt'
        """

        if self._text:
            mode = "r"
        else:
            mode = "rb"

        with open(filename, mode, encoding=self._encoding) as f:
            return (iter(f) | self)

    def __or__(left, right):
        return PipePy._pipe(left, right)

    def __ror__(right, left):
        return PipePy._pipe(left, right)

    @staticmethod
    def _pipe(left, right):
        """ Piping functionality. The supported use-cases are:

            1. `left` is a string and `right` is a `PipePy` instance:

                `left` will be used as `right`'s stdin. `left`'s type will be
                converted from/to bytes/str according to `right`'s `_text`
                value. `right` will not be evaluated straight away

            2. `left` is an iterable and `right` is a `PipePy` instance:

                `right` will be evaluated with `_wait=False`. `left` will be
                iterated over and fed into `right`'s process's stdin. Finally,
                `right` will be waited for.

            3. `left` and `right` are both `PipePy` instances:

                If `left` is not evaluated yet, `left`'s stdout file describtor
                will be used as `right`'s stdin. Otherwise, `left`'s captured
                stdout will be used as `right`'s input. `right` will not be
                evaluated

            4. `left` is a `PipePy` instance and `right` is a function

                `left` will be evaluated and `right` will be invoked with
                `returncode`, `stdout` and `stderr` arguments.
        """

        if isinstance(left, PipePy):
            left_is_iterable = False
        else:
            try:
                iter(left)
            except TypeError:
                left_is_iterable = False
            else:
                left_is_iterable = True

        if isinstance(left, PipePy):
            if isinstance(right, PipePy):
                if left._stdout is not None:
                    stdin = left._stdout
                else:
                    left = -left
                    stdin = left._process.stdout
                result = right(_stdin=stdin)
                return result
            elif callable(right):
                error = TypeError(f"Cannot pipe {left!r} to {right!r}: "
                                  "Invalid function signature")
                parameters = inspect.signature(right).parameters
                if not parameters:
                    raise error
                if not all((value.kind ==
                            inspect.Parameter.POSITIONAL_OR_KEYWORD
                            for value in parameters.values())):
                    raise error
                keys = set(parameters.keys())
                if keys <= {'returncode', 'output', 'errors'}:
                    arguments = {'returncode': left.returncode,
                                 'output': left.stdout,
                                 'errors': left.stderr}
                elif keys <= {'stdout', 'stderr'}:
                    left = -left
                    arguments = {'stdout': left._process.stdout,
                                 'stderr': left._process.stderr}
                else:
                    raise error
                kwargs = {key: value
                          for key, value in arguments.items()
                          if key in keys}

                result = right(**kwargs)
                if not left._wait:
                    left.wait()
                return result
            else:
                raise TypeError("Unrecognized operands")
        elif isinstance(left, (bytes, str)):
            if right._text:
                try:
                    left = left.decode(right._encoding)
                except AttributeError:
                    pass
            else:
                try:
                    left = left.encode(right._encoding)
                except AttributeError:
                    pass
            return right(_stdin=left)
        elif left_is_iterable:
            right = -right
            for chunk in left:
                if right._text:
                    try:
                        chunk = chunk.decode(right._encoding)
                    except AttributeError:
                        pass
                else:
                    try:
                        chunk = chunk.encode(right._encoding)
                    except AttributeError:
                        pass
                right._process.stdin.write(chunk)
                if '\n' in chunk:
                    right._process.stdin.flush()
            right.wait()
            return right
        else:
            raise TypeError("Unrecognized operands")

    # Context processor
    def __enter__(self):
        if self._wait:
            self._context = -self
            return self._context.__enter__()
        return self._process.stdin, self._process.stdout, self._process.stderr

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context is not None:
            self._context.wait()
            self._context = None
        else:
            self.wait()
