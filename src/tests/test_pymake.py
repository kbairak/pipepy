import tempfile

from pipepy import cd, export
from pipepy import pymake as pymake_cmd
from pipepy.pymake import pymake

from .utils import strip_leading_spaces


def test_pymake_simple():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("Makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    def hello():
                        print("Hello world")
                """
                    )
                )
            assert str(pymake_cmd.hello) == "Hello world\n"
            pymake("hello")


def test_pymake_default_target():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("Makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    DEFAULT_PYMAKE_TARGET = "hello"

                    def hello():
                        print("Hello world")
                """
                    )
                )
            assert str(pymake_cmd) == "Hello world\n"
            pymake()


def test_pymake_dependencies():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("Makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    def func1():
                        print("func1")

                    def func2(func1):
                        print("func2")
                """
                    )
                )
            assert str(pymake_cmd.func2) == "func1\nfunc2\n"
            pymake("func2")


def test_pymake_dependencies_only_called_once():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("Makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    def func1():
                        print("func1")

                    def func2(func1):
                        print("func2")

                    def func3(func1, func2):
                        print("func3")
                """
                    )
                )
            assert str(pymake_cmd.func3) == "func1\nfunc2\nfunc3\n"
            pymake("func3")


def test_custom_makefile():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("custom_makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    def hello():
                        print("Hello world")
                """
                    )
                )
            assert str(pymake_cmd("custom_makefile.py").hello) == "Hello world\n"
            pymake("custom_makefile.py", "hello")


def test_pymake_kwarg_from_command_line():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("Makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    def hello(msg="world"):
                        print(f"Hello {msg}")
                """
                    )
                )
            assert str(pymake_cmd.hello) == "Hello world\n"
            pymake("hello")
            assert str(pymake_cmd.hello("msg=Bill")) == "Hello Bill\n"
            pymake("hello", "msg=bill")


def test_pymake_kwarg_from_envronment():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("Makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    def hello(msg="world"):
                        print(f"Hello {msg}")
                """
                    )
                )
            assert str(pymake_cmd.hello) == "Hello world\n"
            pymake("hello")
            with export(msg="Bill"):
                assert str(pymake_cmd.hello) == "Hello world\n"
                pymake("hello")
                assert str(pymake_cmd("-e").hello) == "Hello Bill\n"
                pymake("-e", "hello")


def test_pymake_var_from_command_line():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("Makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    msg = "world"

                    def hello():
                        print(f"Hello {msg}")
                """
                    )
                )
            assert str(pymake_cmd.hello) == "Hello world\n"
            pymake("hello")
            assert str(pymake_cmd.hello("msg=Bill")) == "Hello Bill\n"
            pymake("hello", "msg=bill")


def test_pymake_var_from_envronment():
    with tempfile.TemporaryDirectory() as tmpdir:
        with cd(tmpdir):
            with open("Makefile.py", "w") as f:
                f.write(
                    strip_leading_spaces(
                        """
                    msg = "world"

                    def hello():
                        print(f"Hello {msg}")
                """
                    )
                )
            assert str(pymake_cmd.hello) == "Hello world\n"
            pymake("hello")
            with export(msg="Bill"):
                assert str(pymake_cmd.hello) == "Hello world\n"
                pymake("hello")

                assert str(pymake_cmd("-e").hello) == "Hello Bill\n"
                pymake("-e", "hello")
