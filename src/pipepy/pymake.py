import importlib.util
import inspect
import sys

Makefile = None
already_run = {}
command_args = {}


def _load_makefile():
    global Makefile

    spec = importlib.util.spec_from_file_location('Makefile', './Makefile.py')
    Makefile = importlib.util.module_from_spec(spec)
    sys.modules['Makefile'] = Makefile
    spec.loader.exec_module(Makefile)


def pymake():
    _pymake(*sys.argv[1:])


def _pymake(*args):
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


def pymake_complete():
    _load_makefile()
    word = sys.argv[-2]
    print(" ".join((attr for attr in dir(Makefile) if attr.startswith(word))))
