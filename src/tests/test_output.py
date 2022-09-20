import io
import pathlib
import time

import pipepy
from pipepy import PipePy, cat, echo, false, grep, ls, rm, true

echo_messages = PipePy("python", "src/tests/playground/echo_messages.py")


def test_return_properties():
    assert true.returncode == 0
    assert false.returncode != 0
    assert echo("hello world").stdout == "hello world\n"
    assert (
        echo_messages(stream="stderr", count=1, message="hello world").stderr
        == "hello world\n"
    )


def test_bool():
    assert true
    assert not false


def test_str():
    assert str(echo("hello world")) == "hello world\n"
    assert str(echo("καλημέρα", _text=False)) == "καλημέρα\n"
    assert (
        str("καλημέρα".encode("iso-8859-7") | cat(_text=False, _encoding="iso-8859-7"))
        == "καλημέρα"
    )


def test_as_table():
    (
        ("field1 field2\nvalue1 value2\nvalue3 value4\n" | cat).as_table()
        == [
            {"field1": "value1", "field2": "value2"},
            {"field1": "value3", "field2": "value4"},
        ]
    )


def test_iter():
    assert list(echo("a\nb\nc")) == ["a\n", "b\n", "c\n"]
    assert list(echo("a", "b", "c").iter_words()) == ["a", "b", "c"]

    tic = None
    delay = 0.01
    for i, line in enumerate(
        echo_messages(count=3, delay=delay, message="hello world {}")
    ):
        toc = time.time()
        if tic is not None:
            # Verify that the message is indeed delayed
            assert toc - tic > 0.8 * delay
        assert line.strip() == f"hello world {i}"
        tic = time.time()


def test_redirects_filenames():
    filename = "src/tests/playground/output.txt"
    echo("hello world") > filename
    with open(filename) as f:
        assert f.read().strip() == "hello world"

    echo("hello world") >> filename
    with open(filename) as f:
        assert f.read().strip() == "hello world\nhello world"

    assert str(cat < filename).strip() == "hello world\nhello world"

    rm(filename)()


def test_redirects_pathlib():
    filename = pathlib.Path("src/tests/playground/output.txt")
    echo("hello world") > filename
    with open(filename) as f:
        assert f.read().strip() == "hello world"

    echo("hello world") >> filename
    with open(filename) as f:
        assert f.read().strip() == "hello world\nhello world"

    assert str(cat < filename).strip() == "hello world\nhello world"

    rm(filename)()


def test_redirects_buffers():
    buf = io.StringIO("foo")
    echo("hello world") > buf
    buf.seek(0)
    assert buf.read() == "hello world\n"

    buf = io.BytesIO(b"foo")
    echo("hello world", _text=False) > buf
    buf.seek(0)
    assert buf.read() == b"hello world\n"

    buf = io.StringIO("foo ")
    echo("hello world") >> buf
    buf.seek(0)
    assert buf.read() == "foo hello world\n"

    buf = io.BytesIO(b"foo ")
    echo("hello world", _text=False) >> buf
    buf.seek(0)
    assert buf.read() == b"foo hello world\n"

    assert str(grep("aaa") < io.StringIO("aaa\nbbb")) == "aaa\n"


def test_streams():
    result = ls(_stream=True)
    assert result
    assert result._stdout is None
    assert result._stderr is None

    pipepy.set_always_stream(True)
    result = ls()
    assert result
    assert result._stdout is None
    assert result._stderr is None

    result = ls(_stream=False)
    assert result
    assert result._stdout
    assert result._stderr is not None
    assert not result._stderr

    pipepy.set_always_stream(False)
