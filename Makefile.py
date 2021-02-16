import pipepy
from pipepy import python, rm

pipepy.set_always_stream(True)
pipepy.set_always_raise(True)


DEFAULT_PYMAKE_TARGET = "watchtest"


def test():
    from pipepy import pytest
    pytest()


def covtest():
    from pipepy import pytest
    pytest(cov="src/pipepy", cov_report="term-missing")()


def html(covtest):
    from pipepy import coverage, xdg_open
    coverage.html()
    xdg_open("htmlcov/index.html")()


def watchtest():
    from pipepy import pytest_watch
    pytest_watch()


def debugtest():
    from pipepy import pytest
    pytest('-s')()


def checks():
    from pipepy import flake8, isort
    flake8()
    isort('.')()


def clean():
    rm('-rf', "build", "dist")()


def build(clean):
    python('-m', "build")()


def publish(build):
    python('-m', "twine").upload("dist/*")()
