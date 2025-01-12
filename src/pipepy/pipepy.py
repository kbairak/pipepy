import inspect
import io
import pathlib
import reprlib
import types
from collections.abc import Iterable, Iterator, Sequence
from copy import copy
from glob import glob
from subprocess import PIPE, Popen, TimeoutExpired
from typing import IO, Any, Callable, Self

from .exceptions import PipePyError
from .utils import _File

ALWAYS_RAISE = False
ALWAYS_STREAM = False
INTERACTIVE = False

_JOBS: dict[int, "PipePy"] = {}


def jobs() -> list["PipePy"]:
    return list(_JOBS.values())


def wait_jobs(timeout=None):
    for command in jobs():
        command.wait(timeout)


def set_always_raise(value):
    global ALWAYS_RAISE
    ALWAYS_RAISE = value


def set_always_stream(value):
    global ALWAYS_STREAM
    ALWAYS_STREAM = value


def set_interactive(value):
    global INTERACTIVE
    INTERACTIVE = value


# Forward calls to background process
def _map_to_background_process(method):
    """Expose the `send_signal`, `terminate` and `kill` methods of Popen
    objects to PipePy objects.
    """

    def func(self, *args, **kwargs):
        if self._process is None:
            raise TypeError(f"Cannot call '{method}' on non-background process")
        getattr(self._process, method)(*args, **kwargs)

    return func


class PipePy:
    # Init and copies
    def __init__(
        self,
        *args: Iterable,
        _lazy: bool = False,
        _input: Self | Iterable | _File | None = None,
        _stream_stdout: bool | None = None,
        _stream_stderr: bool | None = None,
        _stream: bool | None = None,
        _text: bool = True,
        _encoding: str = "UTF-8",
        _raise: bool | None = None,
        **kwargs: dict[str, Any],
    ):
        """Initialize a PipePy object.

        Usually you will not need to call this directly, but invoke
        `__call__` to customize existing PipePy objects. Most arguments are
        not meant to be set by users directly, but by other functions or
        operators.

        The ones you may set yourself are:

        - args, kwargs: Customizes the command that is passed to the shell

        - _stream_stdout, _stream_stderr: Determines whether the relevant
            output stream of the command will be stored or whether it will
            be passed on to the relevant stream of the underlying Python
            process. `_stream` applies to both streams takes precedence
            over the other two. If you get a copy of the command with
            `.stream()`, the `_stream` parameter will be set. If not set,
            the `pipepy.ALWAYS_STREAM` value will be respected (defaults to
            False)

        - _text, _encoding: Whether the `str` or the `bytes` type will be
            used for input and output. `_text` defaults to `True`. The
            associated subprocesses and files will be opened with this
            setting. Also, strings or byte sequences passed as input/output
            will be automatically converted to the correct type, using the
            encoding described by `_encoding` (defaults to `UTF-8`)

        - _raise: Whether a command will raise an exception if its
            returncode is not 0. If not set, the `pipepy.ALWAYS_RAISE`
            setting will be respsected (defaults to `False`). If you don't
            set it, or if you set it to `False`, you can still raise an
            exception by calling `command.raise_for_returncode()` (similar
            to `request`'s `response.raise_for_status()`)

        The ones that are set by functions or operators are:

        - _lazy: Whether this instance will be evaluated again after having
            been evaluated once. PipePy objects created with the
            constructor will have this set to False but copies returned
            from `__call__` or other helper functions will have this set to
            True

        - _input: Where the command's input comes from. Will be populated
              by pipe operations `"foo\nbar\n" | grep("foo")` will be
              equivalent to`grep("foo", _input="foo\nbar\n")`)

        - _stream: Whether the output streams will be captured or passed on
            to the relevant streams of the underlying Python process. Will
            be set to True to the copy returned by `.stream()`
        """

        self._args = self._convert_args(args, kwargs)
        self._lazy = _lazy
        self._input = _input
        self._stream_stdout = _stream_stdout
        self._stream_stderr = _stream_stderr
        self._stream = _stream
        self._text = _text
        self._encoding = _encoding
        self._raise = _raise

        self._process: Popen | None = None
        self._input_consumed = False

        self._returncode: int | None = None
        self._stdout = None
        self._stderr = None

    def __call__(
        self,
        *args: Sequence,
        _input=None,
        _stream_stdout: bool | None = None,
        _stream_stderr: bool | None = None,
        _stream: bool | None = None,
        _text: bool | None = None,
        _encoding: str | None = None,
        _raise: bool | None = None,
        **kwargs: dict[str, Any],
    ) -> Self:
        """Make and return a copy of `self`, overriding some of its
        parameters.

        The copy will be lazy, ie if evaluated once and its output accessed
        a second time, the second time will return the stored values and
        not trigger another evaluation.

        If called without any arguments, will immediately trigger an
        evaluation.
        """

        force = (
            not args
            and _input is None
            and _stream_stdout is None
            and _stream_stderr is None
            and _stream is None
            and _text is None
            and _encoding is None
            and _raise is None
            and not kwargs
        )

        actual_args = self._args + list(args)
        if _input is None:
            _input = self._input
        if _stream_stdout is None:
            _stream_stdout = self._stream_stdout
        if _stream_stderr is None:
            _stream_stderr = self._stream_stderr
        if _stream is None:
            _stream = self._stream
        if _text is None:
            _text = self._text
        if _encoding is None:
            _encoding = self._encoding
        if _raise is None:
            _raise = self._raise

        result = self.__class__(
            *actual_args,
            _lazy=True,
            _input=_input,
            _stream_stdout=_stream_stdout,
            _stream_stderr=_stream_stderr,
            _stream=_stream,
            _text=_text,
            _encoding=_encoding,
            _raise=_raise,
            **kwargs,
        )
        if force:
            result._evaluate()
        return result

    def __sub__(self, right: str) -> "PipePy":
        """Alternate method of adding switches to commands:

            >>> ls - 'l'
            >>> # is equivalent to
            >>> ls('-l')

        If the right operand is longer than 1 character, 2 dashes will be
        used:

            >>> ls - 'escape'
            >>> # is equivalent to
            >>> ls('--escape')
        """

        left = self

        if len(right) == 1:
            return left(f"-{right}")
        else:
            return left(f"--{right}")

    def __getattr__(self, attr: str) -> Self:
        """Alternate way of pasing arguments to commands. Essentially

            >>> git = PipePy('git')
            >>> git.status

        should be equivalent to

            >>> git('status')
        """

        return self.__class__(
            *(self._args + [attr]),
            _lazy=self._lazy,
            _input=copy(self._input),
            _stream_stdout=self._stream_stdout,
            _stream_stderr=self._stream_stderr,
            _stream=self._stream,
            _text=self._text,
            _encoding=self._encoding,
            _raise=self._raise,
        )

    def __copy__(self) -> Self:
        return self.__class__(
            *self._args,
            _lazy=True,
            _input=copy(self._input),
            _stream_stdout=self._stream_stdout,
            _stream_stderr=self._stream_stderr,
            _stream=self._stream,
            _text=self._text,
            _encoding=self._encoding,
        )

    @staticmethod
    def _convert_args(args: Iterable, kwargs: dict[str, Any]) -> list[str]:
        """Do some fancy processing of arguments. The intention is to enable
        things like:

            >>> PipePy('sleep', 10)
            >>> # Equivalent to
            >>> PipePy('sleep', '10')

            >>> PipePy('ls', I='foo')
            >>> # Equivalent to
            >>> PipePy('ls', '-I', 'foo')

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

        final_args: list[str] = []
        for arg in args:
            arg = str(arg)
            if globbed := glob(arg, recursive=True):
                final_args.extend(globbed)
            else:
                final_args.append(arg)

        for key, value in kwargs.items():
            key = key.replace("_", "-")
            if value is True:
                if len(key) == 1:
                    final_args.append(f"-{key}")
                else:
                    final_args.append(f"--{key}")
            elif value is False:
                final_args.append(f"--no-{key}")
            elif len(key) == 1:
                final_args.extend([f"-{key}", value])
            else:
                final_args.append(f"--{key}={value}")
        return final_args

    # Lifetime implementation
    def _evaluate(self):
        """Start an evaluation, Lazy commands that have been evaluated before
        will abort. The lifetime of a command being evaluated consists of 3
        steps:

        - Starting the process
        - Feeding the input to the process's stdin, if it has been
          configured to do so with pipes etc
        - Waiting for the command to finish and capture its result

        Piping operations usually don't call this method to evaluate but
        manually invoke the first 2 steps, utilizing the output of the
        process and then calling `wait`, which is a public method.
        """

        if self._returncode is not None and self._lazy:
            return

        self._start_background_job()
        self._feed_input()
        self.wait()

    def _start_background_job(self, stdin_to_pipe: bool = False):
        """Starts the process that will carry out the command. If the process
        has already been started, it will abort. If the input to this
        command is another PipePy object, its background process will be
        started too via this method (so it will recursively start all
        background processes of a pipe chain if necessary) and its stdout
        will be connected to our stdin.
        """

        if self._process is not None and self._lazy:
            return

        stdin: IO[Any] | int | None
        if isinstance(self._input, PipePy):
            if self._input._returncode is not None:
                stdin = PIPE
            else:
                self._input._start_background_job(stdin_to_pipe=stdin_to_pipe)
                assert self._input._process is not None
                stdin = self._input._process.stdout
        elif (
            isinstance(self._input, Iterable)
            or stdin_to_pipe
            or isinstance(self._input, _File)
        ):
            stdin = PIPE
        else:
            stdin = None

        if self._stream_stdout is None and self._stream is None:
            stdout = None if ALWAYS_STREAM else PIPE
        elif self._stream_stdout is None and self._stream is not None:
            stdout = None if self._stream else PIPE
        else:
            stdout = None if self._stream_stdout else PIPE

        if self._stream_stderr is None and self._stream is None:
            stderr = None if ALWAYS_STREAM else PIPE
        elif self._stream_stderr is None and self._stream is not None:
            stderr = None if self._stream else PIPE
        else:
            stderr = None if self._stream_stderr else PIPE

        self._process = Popen(
            self._args, stdin=stdin, stdout=stdout, stderr=stderr, text=self._text
        )
        _JOBS[self._process.pid] = self

    def _feed_input(self):
        """If the command has been configured to receive special input via its
        `_input` parameter, ie via pipes or input redirects, the input will
        be passed to the command during this step.
        """

        if self._input_consumed and self._lazy:
            return

        left = self._input
        if isinstance(left, PipePy):
            if left._returncode is not None:
                chunk = left.stdout
                if self._text:
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode(self._encoding)
                else:
                    if isinstance(chunk, str):
                        chunk = chunk.encode(self._encoding)
                assert self._process is not None
                assert self._process.stdin is not None
                self._process.stdin.write(chunk)
                self._process.stdin.flush()
                self._process.stdin.close()
            else:
                left._start_background_job()
                left._feed_input()
        elif isinstance(left, _File):
            with open(
                left.filename,
                mode="r" if self._text else "rb",
                encoding=self._encoding if self._text else None,
            ) as f:
                assert self._process is not None
                assert self._process.stdin is not None
                for line in f:
                    self._process.stdin.write(line)
                    self._process.stdin.flush()
                self._process.stdin.close()
        elif isinstance(left, Iterable):
            if isinstance(left, (str, bytes)):
                left = [left]
            assert self._process is not None
            assert self._process.stdin is not None
            for chunk in left:
                if self._text:
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode(self._encoding)
                else:
                    if isinstance(chunk, str):
                        chunk = chunk.encode(self._encoding)
                self._process.stdin.write(chunk)
                self._process.stdin.flush()
            self._process.stdin.close()

        self._input_consumed = True

    # Control lifetime
    def delay(self) -> Self:
        """Create and return a copy of `self` and perform 2 out of 3 steps of
        its evaluation, ie don't wait for its result.

        You can then manually `.wait()` for this command to finish, or you
        can try to evaluate it (by accessing its output), which will cause
        its normal `_evaluate` method to run, which will skip the first 2
        steps and internally call `.wait()` before capturing its output

            >>> sleep = PipePy('sleep')
            >>> job = sleep(5).delay()
            >>> if job:  # This will wait for the command to finish
            ...     print("Job finished")

        You should take care to manually wait for background commands to
        finish yourself. If the python process ends, all its child
        processes will end too and your command may be killed abrubtly.
        """

        result = copy(self)
        result._start_background_job()
        result._feed_input()
        return result

    def wait(self, timeout=None):
        """Wait for a process to finish and store the result.

        This is called internally by pipe operations, but can also be
        called by the user for a background command that has been created
        with `.delay()`.

            >>> sleep = PipePy('sleep')
            >>> job = sleep(5).delay()
            >>> job.wait()
            >>> print("Job finished")
        """

        assert self._process is not None
        try:
            self._stdout, self._stderr = self._process.communicate(timeout=timeout)
            self._returncode = self._process.wait()
        except TimeoutExpired:
            raise
        except Exception:
            if self._process.stdout is not None:
                self._stdout = self._process.stdout.read()
            else:
                self._stdout = "" if self._text else b""
            if self._process.stderr is not None:
                self._stderr = self._process.stderr.read()
            else:
                self._stderr = "" if self._text else b""
            self._returncode = self._process.wait(timeout)
        try:
            del _JOBS[self._process.pid]
        except KeyError:
            pass

        job = self
        while isinstance(job._input, PipePy):
            job = job._input
            job.wait(timeout)

        raise_exception = self._raise
        if raise_exception is None:
            raise_exception = ALWAYS_RAISE
        if raise_exception:
            self.raise_for_returncode()

    def raise_for_returncode(self):
        """Raise an exception if the command's returncode is not 0.

        Will be called automatically for all commands that are not created
        with `.quiet` if `pipepy.ALWAYS_RAISE` is True.

        The exception will have the `returncode`, `stdout` and `stderr`
        properties.
        """

        if self.returncode != 0:
            raise PipePyError(self._returncode, self._stdout, self._stderr)

    # Getting output
    @property
    def returncode(self) -> int:
        """Evaluate the command and return its returncode."""

        self._evaluate()
        assert self._returncode is not None
        return self._returncode

    @property
    def stdout(self) -> str | bytes:
        """Evaluate the command and return its stdout."""

        self._evaluate()
        assert isinstance(self._stdout, (str, bytes))
        return self._stdout

    @property
    def stderr(self) -> str | bytes:
        """Evaluate the command and return its stderr."""

        self._evaluate()
        assert self._stderr is not None
        return self._stderr

    def __str__(self) -> str:
        """Return stdout as string, even if the command has `_text=False`."""

        if isinstance(self.stdout, bytes):
            try:
                return self.stdout.decode(self._encoding)
            except UnicodeDecodeError:
                return str(self.stdout)
        else:
            return self.stdout

    def __bool__(self) -> bool:
        """Use in boolean expressions.

        Usage:

            >>> git = PipePy('git')
            >>> grep = PipePy('grep')

            >>> if git('branch') | grep('my_feature'):
            ...     print("Branch found")
        """

        return self.returncode == 0

    def __iter__(self) -> Iterator[str | bytes]:
        """Support the iteration interface:

        Usage:

            >>> ls = PipePy('ls')
            >>> for name in ls:
            ...     print(ls.upper())
        """

        if self._stdout is not None:
            yield from self._stdout.splitlines()
        else:
            self._start_background_job()
            self._feed_input()
            assert self._process is not None
            assert self._process.stdout is not None
            yield from self._process.stdout
            self.wait()

    def iter_words(self) -> Iterator[str | bytes]:
        """Iterate over the *words* of the output of the command.

        >>> ps = PipePy('ps')
        >>> list(ps.iter_words())
        <<< ['PID', 'TTY', 'TIME', 'CMD',
        ...  '11439', 'pts/5', '00:00:00', 'zsh',
        ...  '15532', 'pts/5', '00:00:10', 'ptipython',
        ...  '15539', 'pts/5', '00:00:00', 'ps']
        """

        for line in self:
            yield from line.split()

    def as_table(self) -> list[dict]:
        """Usage:

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

    def __repr__(self) -> str:
        """Return some useful information about the PipePy object.

        If `pipepy.INTERACTIVE` is set, it will evaluate and print the
        command's output, offering a semblance of an interactive shell.

            >>> ls = PipePy('ls')
            >>> ls
            <<< PipePy('ls')
            >>> pipepy.INTERACTIVE = True
            >>> ls
            <<< main.py files.txt
        """

        if INTERACTIVE:
            result = self._interactive_repr()
            if isinstance(result, bytes):
                return result.decode(self._encoding)
            else:
                return result
        else:
            return self._normal_repr()

    def _normal_repr(self):
        result = [self.__class__.__name__, "("]
        result.append(", ".join((repr(arg) for arg in self._args)))
        if self._input is not None:
            result.append(f", _input={self._input!r}")
        if self._returncode is not None:
            result.append(f", _returncode={self._returncode}")
        if self._stdout:
            result.append(f", _stdout={reprlib.repr(self._stdout)}")
        if self._stderr:
            result.append(f", _stderr={reprlib.repr(self._stderr)}")
        result.append(")")
        return "".join(result)

    def _interactive_repr(self) -> str | bytes:
        if isinstance(self.stdout, str) and isinstance(self.stderr, str):
            return self.stdout + self.stderr
        elif isinstance(self.stdout, bytes) and isinstance(self.stderr, bytes):
            return self.stdout + self.stderr
        else:
            raise ValueError("stdout and stderr must be of the same type")

    # Redirect output
    def __gt__(self, right):
        """Write output to file or file-like object

        Usage:

            >>> ps = PipePy('ps')
            >>> ps > 'progs.txt'
        """

        left = self

        if isinstance(right, (pathlib.Path, str)):
            with open(
                right,
                "w" if left._text else "wb",
                encoding=left._encoding if left._text else None,
            ) as f:
                if left._returncode is None:
                    for line in left:
                        f.write(line)
                else:
                    f.write(left.stdout)
        elif isinstance(right, io.IOBase):
            right.seek(0)
            right.truncate()
            if left._returncode is None:
                for line in left:
                    right.write(line)
            else:
                right.write(left.stdout)
        else:
            return NotImplemented

    def __rshift__(self, right):
        """Append output to file or file-like object

        Usage:

            >>> ps = PipePy('ps')
            >>> ps >> 'progs.txt'
        """

        left = self

        if isinstance(right, (pathlib.Path, str)):
            with open(
                right,
                "a" if left._text else "ab",
                encoding=left._encoding if left._text else None,
            ) as f:
                if left._returncode is None:
                    for line in left:
                        f.write(line)
                else:
                    f.write(left.stdout)
        elif isinstance(right, io.IOBase):
            right.read()  # Move pointer to end
            if left._returncode is None:
                for line in left:
                    right.write(line)
            else:
                right.write(left.stdout)
        else:
            return NotImplemented

    def __lt__(self, right):
        """Read input from file or file-like object

        Usage:

            >>> grep = PipePy('grep')
            >>> grep('python') < 'progs/txt'
        """

        left = self

        if isinstance(right, (pathlib.Path, str)):
            return left(_input=_File(right))
        elif isinstance(right, io.IOBase):
            return left(_input=iter(right))
        else:
            return NotImplemented

    # Pipes
    def __or__(self, right: "PipePy | Callable | types.GeneratorType") -> "PipePy":
        left = self
        return PipePy._pipe(left, right)

    def __ror__(self, left: "PipePy | Iterable") -> "PipePy":
        right = self
        return PipePy._pipe(left, right)

    def __getitem__(self, index: "PipePy | Iterable"):
        """Use square-bracket notation for input. Essentially

            >>> foo | bar

        Should be equivalent to

            >>> bar[foo]
        """

        return PipePy._pipe(index, self)

    @staticmethod
    def _pipe(
        left: "PipePy | Iterable", right: "PipePy | Callable | types.GeneratorType"
    ):
        """Support pipe operations. Depending on the operands, slightly
        different behaviors emerge:

        1. If both operands are PipePy objects, the returned object will,
           upon evaluation, start both operands as background processes and
           connect the left's stdout to the right's stdin

            >>> ls = PipePy('ls')
            >>> grep = PipePy('grep')
            >>> print(ls | grep('files'))
            <<< files.txt

        2. If only the right operand is a PipePy object, the left operand
           will be used as input. The left operand can be any iterable
           object, including lists, strings or generators

            >>> grep = PipePy('grep')
            >>> print(["foo\n", "bar\n"] | grep("foo"))
            <<< foo

            >>> def my_input():
            ...     yield "foo\n"
            ...     yield "bar\n"
            >>> print(my_input() | grep("foo"))
            <<< foo

        3. If only the the left operand is a PipePy object and the right
           object is a function, then the command will be evaluated and its
           output will be passed as arguments to the function:

           - If the function's arguments are a subset of [returncode,
             output, errors], the command will be waited and its output
             will be passed at once to the function
           - If the function's arguments are a subset of [stdout, stderr],
             the command will be run in the background and its stdout and
             stderr streams will be made available to the function

           The ordering of the arguments doesn't matter since the
           function's signature will be inspected to determine the
           appropriate behavior

        4. If only the the left operand is a PipePy object and the right
           object is a generator (the return value of a function that
           `yield`s), then the generator will receive non-empty lines from
           the command's output and the return value of the pipe operation
           will be another generator that will yield whatever the original
           generator yielded

            >>> def my_generator():
            ...     line = yield
            ...     while True:
            ...         line = (yield line.upper())

            >>> list("aaa\nbbb" | cat | my_generator())
            <<< ["AAA", "BBB"]
        """

        if isinstance(left, PipePy) and isinstance(right, PipePy):
            return right(_input=left)
        elif isinstance(right, PipePy):
            if isinstance(left, Iterable):
                return right(_input=left)
        elif isinstance(left, PipePy):
            if callable(right):
                return left._send_output_to_function(right)
            elif isinstance(right, types.GeneratorType):
                return left._send_output_to_generator(right)
        else:
            return NotImplemented

    # Help with pipes
    def _send_output_to_function(self, func: Callable) -> Any:
        """Implement the "pipe to function" functionality"""

        error = TypeError(f"Cannot pipe to {func!r}: Invalid function signature")
        parameters = inspect.signature(func).parameters
        if not parameters:
            raise error
        if not all(
            (
                value.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                for value in parameters.values()
            )
        ):
            raise error
        keys = set(parameters.keys())
        arguments: dict[str, Any]
        if keys <= {"returncode", "output", "errors"}:
            arguments = {
                "returncode": self.returncode,
                "output": self.stdout,
                "errors": self.stderr,
            }
            kwargs = {key: value for key, value in arguments.items() if key in keys}
            return func(**kwargs)
        elif keys <= {"stdout", "stderr"}:
            self._start_background_job()
            self._feed_input()
            assert self._process is not None
            arguments = {"stdout": self._process.stdout, "stderr": self._process.stderr}
            kwargs = {key: value for key, value in arguments.items() if key in keys}
            result = func(**kwargs)
            if isinstance(result, types.GeneratorType):
                # Make returned generator wait for the current command on exit
                def generator():
                    yield from result
                    self.wait()

                return generator()
            else:
                self.wait()
                return result
        else:
            raise error

    def _send_output_to_generator(self, generator: types.GeneratorType) -> Any:
        """Implement the "pipe to generator" functionality"""

        def result():
            self._start_background_job()
            self._feed_input()
            assert self._process is not None
            stdout = (
                line.strip() + "\n"
                for line in self._process.stdout or []
                if line.strip()
            )
            try:
                next_input = next(generator)
            except StopIteration:
                generator.close()
                return
            while True:
                if next_input is not None:
                    yield next_input
                try:
                    next_input = generator.send(next(stdout))
                except StopIteration:
                    break
            generator.close()

        return result()

    # `with` statements
    def __enter__(self):
        """Start a job in the background and allow the code block to interact
        with *both* its input and output:

            >>> grep = PipePy('grep')
            >>> with grep("foo") as (stdin, stdout, stderr):
            ...     stdin.write("foo\n")
            ...     stdin.write("bar\n")
            ...     stdin.close()
            ...     print(stdout.read())
            <<< foo
        """

        self._start_background_job(stdin_to_pipe=True)

        job = self
        while isinstance(job._input, PipePy):
            job = job._input

        assert job._process is not None and self._process is not None

        return job._process.stdin, self._process.stdout, self._process.stderr

    def __exit__(self, exc_type, exc_val, exc_tb):
        job = self
        while isinstance(job._input, PipePy):
            job = job._input

        assert job._process is not None
        if job._process.stdin is not None:
            job._process.stdin.close()

        self.wait()
        job = self
        while isinstance(job._input, PipePy):
            job = job._input
            job.wait()

    send_signal = _map_to_background_process("send_signal")
    terminate = _map_to_background_process("terminate")
    kill = _map_to_background_process("kill")
