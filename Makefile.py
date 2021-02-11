from pipepy import (coverage, firefox, flake8, isort, pytest, pytest_watch,
                    python, rm)


DEFAULT_PYMAKE_TARGET = "test"


def test():
    pytest._s()


def covtest():
    pytest(cov="src/pipepy", cov_report="term-missing")._s()


def covtest_and_show(covtest):
    coverage.html._s()
    firefox("htmlcov/index.html")._s()


def watchtest():
    pytest_watch._s()


def debugtest():
    pytest('-s')._s()


def checks():
    flake8._s()
    isort._s()


def clean():
    rm('-rf', "build", "dist")._s()


def build(clean):
    python('-m', "build")._s()


def publish(build):
    python('-m', "twine").upload("dist/*")._s()
