def is_iterable(value):
    try:
        iter(value)
    except TypeError:
        return False
    else:
        return True


class _File:
    """ Simple container for a filename. Mainly needed to be able to run
        `isinstance(..., _FILE)`
    """

    def __init__(self, filename):
        self.filename = filename
