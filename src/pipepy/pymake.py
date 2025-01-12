import importlib.util
import inspect
import os
import sys
from collections.abc import Sequence
from types import ModuleType
from typing import Any, Union

usage = """
Usage: pymake [-e] [MAKEFILE] [TARGET_OR_PARAMETER...]

Options:

  -e/--use-env:        Use environment variables for makefile parameters

  MAKEFILE:            File to use [default: Makefile.py]

  TARGET_OR_PARAMETER: Targets to execute, in order.
                       If it has the form 'key=value', then it is to be used as
                       a makefile parameter
"""


Makefile: Union[ModuleType, None] = None
already_run: dict[str, Any] = {}
command_args: dict[str, Any] = {}


def _get_arg(key: str) -> Any:
    try:
        return command_args[key]
    except KeyError:
        pass

    try:
        return getattr(Makefile, key)
    except AttributeError:
        pass

    raise KeyError(key)


def _load_makefile() -> ModuleType:
    if not os.path.exists("Makefile.py"):
        raise ValueError("Makefile not found")

    spec = importlib.util.spec_from_file_location("Makefile", "Makefile.py")
    assert spec is not None
    assert spec.loader is not None
    Makefile = importlib.util.module_from_spec(spec)
    sys.modules["Makefile"] = Makefile
    spec.loader.exec_module(Makefile)

    return Makefile


def pymake(*args: str):
    global Makefile, already_run, command_args
    Makefile = None
    already_run = {}
    command_args = {}

    if len(args) == 1 and args[0] in ("-h", "--help"):
        print(usage)
        sys.exit(0)

    if _pymake_complete(args):
        return

    Makefile = _load_makefile()

    targets = []
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if hasattr(Makefile, key):
                setattr(Makefile, key, value)
            command_args[key] = value
        else:
            targets.append(arg)

    if not targets:
        try:
            targets = [Makefile.DEFAULT_PYMAKE_TARGET]
        except AttributeError:
            raise ValueError("No targets specified")

    for target in targets:
        _run(target)


def _run(target: str):
    function = getattr(Makefile, target)
    parameters = inspect.signature(function).parameters
    args = []

    for parameter_name, parameter in parameters.items():
        try:
            value = _get_arg(parameter_name)
        except KeyError:
            if parameter.default != inspect._empty:
                value = parameter.default
            else:
                raise

        if callable(value):
            if parameter_name not in already_run:
                already_run[parameter_name] = _run(parameter_name)
            args.append(already_run[parameter_name])
        else:
            args.append(value)

    return function(*args)


def _pymake_complete(args: Sequence[str]) -> bool:
    """Setup completion for shells.

    The first argument must be `--setup-FOO-completion` or `--complete-FOO`
    where FOO is the shell being completed (bash or zsh).

    In order to setup comletion for the respective shell, you must run
    `eval $(pymake --setup-FOO-completion)`.
    """

    if args and args[0] == "--setup-bash-completion":
        print("complete -C 'pymake --complete-bash' pymake")

    elif args and args[0] == "--complete-bash":
        _load_makefile()
        word = args[-2]
        chunks = []
        for attr in dir(Makefile):
            if not attr.startswith(word):
                continue
            func = getattr(Makefile, attr)
            if not callable(func) or getattr(func, "__module__", "") != "Makefile":
                continue
            chunks.append(attr)
        print("\n".join(chunks))

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
            if not callable(func) or getattr(func, "__module__", "") != "Makefile":
                continue
            if func.__doc__:
                doc = func.__doc__
                doc = (
                    doc.replace("\\", "\\\\")
                    .replace(":", "\\:")
                    .replace("'", "'\"'\"'")
                )
                doc = " ".join([line.strip() for line in doc.splitlines()])
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


def main():
    pymake(*sys.argv[1:])  # Separating for tests


if __name__ == "__main__":
    main()
