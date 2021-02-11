import sys
import importlib.util
import inspect

Makefile = None
already_run = {}
command_args = {}


def pymake():
    global Makefile

    spec = importlib.util.spec_from_file_location('Makefile', './Makefile.py')
    Makefile = importlib.util.module_from_spec(spec)
    sys.modules['Makefile'] = Makefile
    spec.loader.exec_module(Makefile)

    has_args = len(sys.argv) > 1
    first_arg_is_target = has_args and '=' not in sys.argv[1]
    if first_arg_is_target:
        target = sys.argv[1]
    else:
        target = Makefile.DEFAULT_PYMAKE_TARGET

    start = 2 if first_arg_is_target else 1
    rest = sys.argv[start:]

    for item in rest:
        key, value = item.split('=')
        command_args[key] = value

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
