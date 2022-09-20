import pipepy
from pipepy import python, rm

pipepy.set_always_stream(True)
pipepy.set_always_raise(True)


DEFAULT_PYMAKE_TARGET = "watchtest"


def test():
    """Run tests"""

    from pipepy import pytest

    pytest()


def covtest():
    """Run tests and produce coverge report"""

    from pipepy import pytest

    pytest(cov="src/pipepy", cov_report="term-missing")()


def html(covtest):
    """Run tests and open coverage report in browser"""

    from pipepy import coverage, xdg_open

    coverage.html()
    xdg_open("htmlcov/index.html")()


def watchtest():
    """Automatically run tests when a source file changes"""

    from pipepy import pytest_watch

    pytest_watch()


def debugtest():
    """Run tests without capturing their output. This makes using an
    interactive debugger possible
    """

    from pipepy import pytest

    s = "s"
    cmd = pytest - s  # noqa: E225
    cmd()


def checks():
    """Run static checks on the code (flake8, isort)"""

    from pipepy import black, flake8, isort

    flake8()
    isort(".", check_only=True)()
    black(".")


def clean():
    """Clean up build directories"""

    rm("-rf", "build", "dist")()


def build(clean):
    """Build package"""

    python("-m", "build")()


def publish(build):
    """Publish package to PyPI"""

    python("-m", "twine").upload("dist/*")()
