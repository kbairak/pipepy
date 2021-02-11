class PipePyError(Exception):
    # https://www.kbairak.net/programming/python/2021/01/21/custom_exceptions.html
    def __init__(self, returncode, stdout, stderr):
        super().__init__(returncode, stdout, stderr)

    @property
    def returncode(self):
        return self.args[0]

    @property
    def stdout(self):
        return self.args[1]

    @property
    def stderr(self):
        return self.args[2]
