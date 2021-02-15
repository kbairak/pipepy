def is_iterable(value):
    try:
        iter(value)
    except TypeError:
        return False
    else:
        return True


class _File:
    def __init__(self, filename):
        self.filename = filename
