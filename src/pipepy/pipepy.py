import inspect
import reprlib
import types
from copy import copy
from glob import glob
from subprocess import PIPE, Popen

from .exceptions import PipePyError
from .utils import _File, is_iterable

ALWAYS_RAISE = False
ALWAYS_STREAM = False
INTERACTIVE = False

_JOBS = {}


def jobs():
    return list(_JOBS.values())


def wait_jobs():
    for command in jobs():
        command.wait()


def set_always_raise(value):
    global ALWAYS_RAISE
    ALWAYS_RAISE = value


def set_always_stream(value):
    global ALWAYS_STREAM
    ALWAYS_STREAM = value


def set_interactive(value):
    global INTERACTIVE
    INTERACTIVE = value


class PipePy:
    # Init and copies
    def __init__(self, *args, _lazy=False, _left=None, _stream_stdout=None,
                 _stream_stderr=None, _stream=None, _text=True,
                 _encoding="UTF-8", _raise=None, **kwargs):
        """ Initialize a PipePy object.

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

            - _left: Where the command's input comes from. Will be populated by
                pipe operations `"foo\nbar\n" | grep("foo")` will be equivalent
                to`grep("foo", _left="foo\nbar\n")`)

            - _stream: Whether the output streams will be captured or passed on
                to the relevant streams of the underlying Python process. Will
                be set to True to the copy returned by `.stream()`
        """

        self._args = self._convert_args(args, kwargs)
        self._lazy = _lazy
        self._left = _left
        self._stream_stdout = _stream_stdout
        self._stream_stderr = _stream_stderr
        self._stream = _stream
        self._text = _text
        self._encoding = _encoding
        self._raise = _raise

        self._process = None
        self._input_fed = False

        self._returncode = None
        self._stdout = None
        self._stderr = None

    def __call__(self, *args, _left=None, _stream_stdout=None,
                 _stream_stderr=None, _stream=None, _text=None, _encoding=None,
                 _raise=None, **kwargs):
        """ Make and return a copy of `self`, overriding some of its
            parameters.

            The copy will be lazy, ie if evaluated once and its output accessed
            a second time, the second time will return the stored values and
            not trigger another evaluation.

            If called without any arguments, will immediately trigger an
            evaluation.
        """

        force = (not args and
                 _left is None and
                 _stream_stdout is None and
                 _stream_stderr is None and
                 _stream is None and
                 _text is None and
                 _encoding is None and
                 _raise is None and
                 not kwargs)

        args = self._args + list(args)
        if _left is None:
            _left = self._left
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

        result = PipePy(*args, _lazy=True, _left=_left,
                        _stream_stdout=_stream_stdout,
                        _stream_stderr=_stream_stderr, _stream=_stream,
                        _text=_text, _encoding=_encoding,
                        _raise=_raise, **kwargs)
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

    def __copy__(self):
        return PipePy(*self._args, _lazy=True, _left=copy(self._left),
                      _stream_stdout=self._stream_stdout,
                      _stream_stderr=self._stderr, _stream=self._stream,
                      _text=self._text, _encoding=self._encoding)

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

    # Lifetime implementation
    def _evaluate(self):
        """ Start an evaluations, Lazy commands that have been evaluated before
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

    def _start_background_job(self, stdin_to_pipe=False):
        """ Starts the process that will carry out the command. If the process
            has already been started, it will abort. If the input to this
            command is another PipePy object, its background process will be
            started too via this method (so it will recursively start all
            background processes of a pipe chain if necessary) and its stdout
            will be connected to our stdin.
        """

        if self._process is not None and self._lazy:
            return

        if isinstance(self._left, PipePy):
            if self._left._returncode is not None:
                stdin = PIPE
            else:
                self._left._start_background_job(stdin_to_pipe=stdin_to_pipe)
                stdin = self._left._process.stdout
        elif (is_iterable(self._left) or
              stdin_to_pipe or
              isinstance(self._left, _File)):
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

        self._process = Popen(self._args,
                              stdin=stdin, stdout=stdout, stderr=stderr,
                              text=self._text)
        _JOBS[self._process.pid] = self

    def _feed_input(self):
        """ If the command has been configured to receive special input via its
            `_left` parameter, ie via pipes or input redirects, the input will
            be passed to the command during this step.
        """

        if self._input_fed and self._lazy:
            return

        left = self._left
        if isinstance(left, PipePy):
            if left._returncode is not None:
                chunk = left.stdout
                if self._text:
                    try:
                        chunk = chunk.decode(self._encoding)
                    except AttributeError:
                        pass
                else:
                    try:
                        chunk = chunk.encode(self._encoding)
                    except AttributeError:
                        pass
                self._process.stdin.write(chunk)
                self._process.stdin.flush()
                self._process.stdin.close()
            else:
                left._start_background_job()
                left._feed_input()
        elif isinstance(left, _File):
            with open(left.filename,
                      mode="r" if self._text else "rb",
                      encoding=self._encoding) as f:
                for line in f:
                    self._process.stdin.write(line)
                    self._process.stdin.flush()
                self._process.stdin.close()
        elif is_iterable(left):
            if isinstance(left, (str, bytes)):
                left = [left]
            for chunk in left:
                if self._text:
                    try:
                        chunk = chunk.decode(self._encoding)
                    except AttributeError:
                        pass
                else:
                    try:
                        chunk = chunk.encode(self._encoding)
                    except AttributeError:
                        pass
                self._process.stdin.write(chunk)
                self._process.stdin.flush()
            self._process.stdin.close()

        self._input_fed = True

    # Control lifetime
    def delay(self):
        """ Create and return a copy of `self` and perform 2 out of 3 steps of
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

    def wait(self):
        """ Wait for a process to finish and store the result.

            This is called internally by pipe operations, but can also be
            called by the user for a background command that has been created
            with `.delay()`.

                >>> sleep = PipePy('sleep')
                >>> job = sleep(5).delay()
                >>> job.wait()
                >>> print("Job finished")
        """

        try:
            self._stdout, self._stderr = self._process.communicate()
        except Exception:
            if self._process.stdout is not None:
                self._stdout = self._process.stdout.read()
            else:
                self._stdout = "" if self._text else b""
            if self._process.stderr is not None:
                self._stderr = self._process.stderr.read()
            else:
                self._stderr = "" if self._text else b""
        try:
            del _JOBS[self._process.pid]
        except KeyError:
            pass
        self._returncode = self._process.wait()

        job = self
        while isinstance(job._left, PipePy):
            job = job._left
            job.wait()

        raise_exception = self._raise
        if raise_exception is None:
            raise_exception = ALWAYS_RAISE
        if raise_exception:
            self.raise_for_returncode()

    def raise_for_returncode(self):
        """ Raise an exception if the command's returncode is not 0.

            Will be called automatically for all commands that are not created
            with `.quiet` if `pipepy.ALWAYS_RAISE` is True.

            The exception will have the `returncode`, `stdout` and `stderr`
            properties.
        """

        if self.returncode != 0:
            raise PipePyError(self._returncode, self._stdout, self._stderr)

    # Getting output
    @property
    def returncode(self):
        """ Evaluate the command and return its returncode. """

        self._evaluate()
        return self._returncode

    @property
    def stdout(self):
        """ Evaluate the command and return its stdout. """

        self._evaluate()
        return self._stdout

    @property
    def stderr(self):
        """ Evaluate the command and return its stderr. """

        self._evaluate()
        return self._stderr

    def __str__(self):
        """ Return stdout as string, even if the command has `_text=False`. """

        try:
            return self.stdout.decode(self._encoding)
        except AttributeError:
            return self.stdout

    def __bool__(self):
        """ Use in boolean expressions.

            Usage:

                >>> git = PipePy('git')
                >>> grep = PipePy('grep')

                >>> if git('branch') | grep('my_feature'):
                ...     print("Branch found")
        """

        return self.returncode == 0

    def __iter__(self):
        """ Support the iteration interface:

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
            yield from self._process.stdout
            self.wait()

    def iter_words(self):
        """ Iterate over the *words* of the output of the command.

                >>> ps = PipePy('ps')
                >>> list(ps.iter_words())
                <<< ['PID', 'TTY', 'TIME', 'CMD',
                ...  '11439', 'pts/5', '00:00:00', 'zsh',
                ...  '15532', 'pts/5', '00:00:10', 'ptipython',
                ...  '15539', 'pts/5', '00:00:00', 'ps']
        """

        for line in self:
            yield from line.split()

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

    def __repr__(self):
        """ Return some useful information about the PipePy object.

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
            return self._interactive_repr()
        else:
            return self._normal_repr()

    def _normal_repr(self):
        result = ["PipePy("]
        result.append(', '.join((repr(arg) for arg in self._args)))
        if self._left is not None:
            result.append(f", _left={self._left!r}")
        if self._returncode is not None:
            result.append(f", _returncode={self._returncode}")
        if self._stdout:
            result.append(f", _stdout={reprlib.repr(self._stdout)}")
        if self._stderr:
            result.append(f", _stderr={reprlib.repr(self._stderr)}")
        result.append(")")
        return ''.join(result)

    def _interactive_repr(self):
        return self.stdout + self.stderr

    # Redirect output
    def __gt__(self, filename):
        """ Write output to file

            Usage:

                >>> ps = PipePy('ps')
                >>> ps > 'progs.txt'
        """

        with open(filename,
                  "w" if self._text else "wb",
                  encoding=self._encoding) as f:
            f.write(self.stdout)

    def __rshift__(self, filename):
        """ Write output to file

            Usage:

                >>> ps = PipePy('ps')
                >>> ps > 'progs.txt'
        """

        with open(filename,
                  "a" if self._text else "ab",
                  encoding=self._encoding) as f:
            f.write(self.stdout)

    def __lt__(self, filename):
        """ Append output to file

            Usage:

                >>> ps = PipePy('ps')
                >>> ps >> 'progs/txt'
        """

        return self(_left=_File(filename))

    # Pipes
    def __or__(left, right):
        return PipePy._pipe(left, right)

    def __ror__(right, left):
        return PipePy._pipe(left, right)

    @staticmethod
    def _pipe(left, right):
        """ Support pipe operations. Depending on the operands, slightly
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
        """

        error = TypeError(f"Cannot perform '|' operation on {left!r} and "
                          f"{right!r}, unsupported operands")
        if isinstance(left, PipePy) and isinstance(right, PipePy):
            return right(_left=left)
        elif isinstance(right, PipePy):
            if is_iterable(left):
                return right(_left=left)
            else:
                raise error
        elif isinstance(left, PipePy):
            if callable(right):
                return left._send_output_to_function(right)
            else:
                raise error
        else:
            raise error

    # Help with pipes
    def _send_output_to_function(self, func):
        """ Implement the "pipe to function" functionality.  """

        error = TypeError(f"Cannot pipe to {func!r}: "
                          "Invalid function signature")
        parameters = inspect.signature(func).parameters
        if not parameters:
            raise error
        if not all((value.kind ==
                    inspect.Parameter.POSITIONAL_OR_KEYWORD
                    for value in parameters.values())):
            raise error
        keys = set(parameters.keys())
        if keys <= {'returncode', 'output', 'errors'}:
            arguments = {'returncode': self.returncode,
                         'output': self.stdout,
                         'errors': self.stderr}
            kwargs = {key: value
                      for key, value in arguments.items()
                      if key in keys}
            return func(**kwargs)
        elif keys <= {'stdout', 'stderr'}:
            self._start_background_job()
            self._feed_input()
            arguments = {'stdout': self._process.stdout,
                         'stderr': self._process.stderr}
            kwargs = {key: value
                      for key, value in arguments.items()
                      if key in keys}
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

    # `with` statements
    def __enter__(self):
        """ Start a job in the background and allow the code block to interact
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
        while isinstance(job._left, PipePy):
            job = job._left

        return job._process.stdin, self._process.stdout, self._process.stderr

    def __exit__(self, exc_type, exc_val, exc_tb):
        job = self
        while isinstance(job._left, PipePy):
            job = job._left
        job._process.stdin.close()

        self.wait()
        job = self
        while isinstance(job._left, PipePy):
            job = job._left
            job.wait()

    # Forward calls to background process
    def _map_to_background_process(method):
        """ Expose the `send_signal`, `terminate` and `kill` methods of Popen
            objects to PipePy objects.
        """

        def func(self, *args, **kwargs):
            if self._process is None:
                raise TypeError(f"Cannot call '{method}' on non-background "
                                f"process")
            getattr(self._process, method)(*args, **kwargs)
        return func

    send_signal = _map_to_background_process('send_signal')
    terminate = _map_to_background_process('terminate')
    kill = _map_to_background_process('kill')
