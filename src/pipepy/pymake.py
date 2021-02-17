import importlib.util
import inspect
import os
import sys

Makefile = None
already_run = {}
command_args = {}


def _load_makefile():
    global Makefile

    if not os.path.exists('Makefile.py'):
        return

    spec = importlib.util.spec_from_file_location('Makefile', './Makefile.py')
    Makefile = importlib.util.module_from_spec(spec)
    sys.modules['Makefile'] = Makefile
    spec.loader.exec_module(Makefile)


def pymake():
    _pymake(*sys.argv[1:])


def _pymake(*args):
    if _pymake_complete(*args):
        return

    _load_makefile()

    targets = []
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=')
            command_args[key] = value
        else:
            targets.append(arg)

    if not targets:
        targets = [Makefile.DEFAULT_PYMAKE_TARGET]

    for target in targets:
        _run(target)


def _run(target):
    global already_run

    function = getattr(Makefile, target)
    parameters = inspect.signature(function).parameters
    args = []

    for parameter_name, parameter in parameters.items():
        if parameter.default == inspect._empty:
            value = command_args.get(parameter_name,
                                     getattr(Makefile, parameter_name))
        else:
            value = command_args.get(parameter_name, parameter.default)

        if callable(value):
            if parameter_name not in already_run:
                already_run[parameter_name] = _run(parameter_name)
            args.append(already_run[parameter_name])
        else:
            args.append(value)

    return function(*args)


def _pymake_complete(*args):
    """ Setup completion for shells.

        The first argument must is `--setup-FOO-completion` or `--complete-FOO`
        where FOO is the shell being completed (bash or zsh).

        In order to setup comletion for the respective shell, you must run
        `eval $(pymake --setup-FOO-completion)`.
    """

    if args and args[0] == "--setup-bash-completion":
        print("complete -C 'pymake --complete-bash' pymake")

    elif args and args[0] == "--complete-bash":
        _load_makefile()
        word = args[-2]
        result = []
        for attr in dir(Makefile):
            if not attr.startswith(word):
                continue
            func = getattr(Makefile, attr)
            if (not callable(func) or
                    getattr(func, '__module__', '') != "Makefile"):
                continue
            result.append(attr)
        print("\n".join(result))

    elif args and args[0] == "--setup-zsh-completion":
        # Register the `_pymake` zsh function to complete pymake calls.
        # `_pymake` will call `pymake --complete-zsh` to dynamically generate
        # completions based on the Makefile
        result = """
            _pymake() {
                eval $(pymake --complete-zsh)
            };
            compdef _pymake pymake
        """
        print(" ".join((line.strip() for line in result.splitlines())))

    elif args and args[0] == "--complete-zsh":
        # Populate the "body" (since it's using `eval`) of the `_pymake` zsh
        # function that is used to generate completions for `pymake`. The body
        # of pymake makes an array of copletions based on the Makefile's
        # targets and their docstrings and then calls the `_describe` zsh
        # builtin
        _load_makefile()
        result = """
            local -a subcmds;
            subcmds=(
        """
        for attr in dir(Makefile):
            func = getattr(Makefile, attr)
            if (not callable(func) or
                    getattr(func, '__module__', '') != "Makefile"):
                continue
            if func.__doc__:
                doc = " ".join([line.strip()
                                for line in func.__doc__.splitlines()])
                result += f" '{attr}:{doc}'"
            else:
                result += f" '{attr}'"
        result += """
            );
            _describe 'command' subcmds
        """
        print(" ".join((line.strip() for line in result.splitlines())))
    else:
        return False
    return True
