class File:
    """Simple container for a filename. Mainly needed to be able to run
    `isinstance(..., FILE)`
    """

    def __init__(self, filename):
        self.filename = filename
