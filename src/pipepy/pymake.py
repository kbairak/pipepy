import sys
import importlib.util
import inspect

Makefile = None


def pymake():
    global Makefile
    spec = importlib.util.spec_from_file_location('Makefile', './Makefile.py')
    Makefile = importlib.util.module_from_spec(spec)
    sys.modules['Makefile'] = Makefile
    spec.loader.exec_module(Makefile)

    try:
        target = sys.argv[1]
    except IndexError:
        try:
            target = Makefile.DEFAULT_PYMAKE_TARGET
        except AttributeError:
            target = None

    if target is None:
        raise ValueError("Target not specified")

    _run(target)


def _run(target, already_run=None):
    if already_run is None:
        already_run = {}

    function = getattr(Makefile, target)
    dependencies = inspect.signature(function).parameters.keys()
    args = []
    for dependency in dependencies:
        if dependency not in already_run:
            already_run[dependency] = _run(dependency, already_run)
        args.append(already_run[dependency])

    return function(*args)
