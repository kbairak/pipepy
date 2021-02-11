from pipepy import (coverage, firefox, flake8, isort, pytest, pytest_watch,
                    python, rm)


DEFAULT_PYMAKE_TARGET = "test"


def test():
    (+pytest)()


def covtest():
    (+pytest(cov="src/pipepy", cov_report="term-missing"))()


def covtest_and_show(covtest):
    (+coverage.html)()
    (+firefox("htmlcov/index.html"))()


def watchtest():
    (+pytest_watch)()


def debugtest():
    (+(pytest - 's'))()


def checks():
    (+flake8)()
    (+isort)()


def clean():
    (+(rm - 'r' - 'f')("build", "dist"))()


def build(clean):
    (+python('-m', "build"))()


def publish(build):
    (+python('-m', "twine").upload("dist/*"))()
