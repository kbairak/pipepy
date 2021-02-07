import __main__
import subprocess
import types
from glob import glob

ENCODING = "utf8"


def set_encoding(encoding):
    global ENCODING
    ENCODING = encoding


class PipePy:
    class _NONE:
        pass

    def __init__(self, *args, _lazy=False, _stdin=None, _stream_stdout=False,
                 _stream_stderr=False, _wait=True, **kwargs):

        self._args = self._convert_args(args, kwargs)
        self._lazy = _lazy
        self._stdin = _stdin
        self._stream_stdout = _stream_stdout
        self._stream_stderr = _stream_stderr
        self._wait = _wait

        self._returncode = None
        self._stdout = None
        self._stderr = None

    def __call__(self, *args, _stdin=_NONE, _stream_stdout=_NONE,
                 _stream_stderr=_NONE, _wait=_NONE, **kwargs):

        force = (not args and
                 not kwargs and
                 _stdin is self._NONE and
                 _stream_stdout is self._NONE and
                 _stream_stderr is self._NONE and
                 _wait is self._NONE)

        args = self._args + list(args)

        if _stdin is self._NONE:
            _stdin = self._stdin
        if _stream_stdout is self._NONE:
            _stream_stdout = self._stream_stdout
        if _stream_stderr is self._NONE:
            _stream_stderr = self._stream_stderr
        if _wait is self._NONE:
            _wait = self._wait

        result = self.__class__(*args,
                                _lazy=True,
                                _stdin=_stdin,
                                _stream_stdout=_stream_stdout,
                                _stream_stderr=_stream_stderr,
                                _wait=_wait,
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

    def _evaluate(self):
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
                                         stdout=stdout, stderr=stderr)

        if self._wait:
            self._wait_process()

    def _wait_process(self):
        if isinstance(self._stdin, bytes):
            stdin = self._stdin
        else:
            stdin = None
        self._stdout, self._stderr = self._process.communicate(stdin)
        self._returncode = self._process.wait()

    @staticmethod
    def _convert_args(args, kwargs):
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

    @property
    def returncode(self):
        self._evaluate()
        return self._returncode

    def __bool__(self):
        """ Use in boolean expressions.

            Usage:
                >>> git = PipePy('git')
                >>> grep = PipePy('grep')

                >>> if git('branch') | grep('my_feature'):
                ...     print("Branch found")
        """

        return self.returncode == 0

    @property
    def stdout(self):
        self._evaluate()
        return self._stdout

    def __str__(self):
        return self.stdout.decode(ENCODING)

    @property
    def stderr(self):
        self._evaluate()
        return self._stderr

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
        return iter(self.stdout.split())

    def __repr__(self):
        if hasattr(__main__, "__file__"):
            return self._normal_repr()
        else:
            return self._interactive_repr()

    def _normal_repr(self):
        result = ["PipePy("]
        if self._args:
            result.append(', '.join((repr(arg) for arg in self._args)))
        else:
            result.append('[]')
        if self._stdin is not None:
            result.extend([", _stdin=", repr(self._stdin)])
        if self._returncode is not None:
            result.extend([", returncode=", repr(self._returncode)])
            if self._stdout is not None:
                result.extend([", stdout=", repr(self._stdout)])
            if self._stderr:
                result.extend([", stderr=", repr(self._stderr)])
        result.append(')')
        return ''.join(result)

    def _interactive_repr(self):
        self._evaluate()
        return str(self) + self.stderr.decode(ENCODING)

    # Redirect output
    def __gt__(self, filename):
        """ Write output to file

            Usage:
                >>> ps = PipePy('ps')

                >>> ps > 'progs.txt'
        """

        with open(filename, 'wb') as f:
            f.write(self.stdout)

    def __rshift__(self, filename):
        """ Append output to file

            Usage:
                >>> ps = PipePy('ps')

                >>> ps >> 'progs/txt'
        """

        with open(filename, 'ab') as f:
            f.write(self.stdout)

    def __lt__(self, filename):
        """ Use file as input

            Usage:
                >>> grep = PipePy('grep')

                >>> grep('python') < 'progs.txt'
        """

        with open(filename, 'rb') as f:
            return self(_stdin=f.read())

    def __or__(left, right):
        return PipePy._pipe(left, right)

    def __ror__(right, left):
        return PipePy._pipe(left, right)

    @staticmethod
    def _pipe(left, right):
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
                    left = left(_wait=False)
                    stdin = left()._process.stdout
                return right(_stdin=stdin)
            elif callable(right):
                return right(returncode=left.returncode,
                             stdout=left.stdout,
                             stderr=left.stderr)
            elif isinstance(right, types.GeneratorType):
                left = left(_wait=False)()
                try:
                    generator_line = next(right)  # Prime generator
                    if generator_line is not None:
                        left._process.stdin.write(generator_line)
                        left._process.stdin.flush()
                    for command_line in left._process.stdout:
                        generator_line = right.send(command_line)
                        if generator_line is not None:
                            left._process.stdin.write(generator_line)
                            left._process.stdin.flush()
                except StopIteration:
                    left._wait_process()
                return left
            else:
                raise TypeError("Unrecognized operands")
        elif isinstance(left, bytes):
            return right(_stdin=left)
        elif left_is_iterable:
            right = right(_wait=False)()
            for chunk in left:
                right._process.stdin.write(chunk)
                right._process.stdin.flush()
            right._wait_process()
            return right
        else:
            raise TypeError("Unrecognized operands")

    def __invert__(self):
        if self._stream_stderr:
            return self(_stream_stdout=True, _stream_stderr=False)
        else:
            return self(_stream_stdout=False, _stream_stderr=True)
