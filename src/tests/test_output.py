import time

from pipepy import PipePy, cat, echo, false, ls, rm, set_always_stream, true

echo_messages = PipePy('python', 'src/tests/playground/echo_messages.py')


def test_return_properties():
    assert true.returncode == 0
    assert false.returncode != 0
    assert echo('hello world').stdout == "hello world\n"
    assert (echo_messages(stream="stderr",
                          count=1,
                          message="hello world").stderr ==
            "hello world\n")


def test_bool():
    assert true
    assert not false


def test_str():
    assert str(echo("hello world")) == "hello world\n"
    assert str(echo("καλημέρα")._b) == "καλημέρα\n"
    assert (str("καλημέρα".encode('iso-8859-7') |
                cat(_text=False, _encoding='iso-8859-7')) ==
            "καλημέρα")


def test_as_table():
    (("field1 field2\nvalue1 value2\nvalue3 value4\n" | cat).as_table() ==
     [{'field1': "value1", 'field2': "value2"},
      {'field1': "value3", 'field2': "value4"}])


def test_iter():
    assert list(echo("a\nb\nc")) == ["a\n", "b\n", "c\n"]

    tic = time.time()
    delay = .01
    for i, line in enumerate(echo_messages(count=3,
                                           delay=delay,
                                           message='hello world {}')):
        toc = time.time()
        assert toc - tic > delay  # Verify that the message is indeed delayed
        tic = toc
        assert line.strip() == f"hello world {i}"

    assert list(echo('a', 'b', 'c').iter_words()) == ["a", "b", "c"]


def test_redirects():
    filename = "src/tests/playground/output.txt"
    echo("hello world") > filename
    with open(filename) as f:
        assert f.read().strip() == "hello world"

    echo("hello world") >> filename
    with open(filename) as f:
        assert f.read().strip() == "hello world\nhello world"

    assert str(cat < filename).strip() == "hello world\nhello world"

    rm(filename)()


def test_streams():
    result = ls._s()
    assert result
    assert result._stdout is None
    assert result._stderr is None

    set_always_stream(True)
    result = ls()
    assert result
    assert result._stdout is None
    assert result._stderr is None

    result = ls._c()
    assert result
    assert result._stdout
    assert result._stderr is not None
    assert not result._stderr

    set_always_stream(False)
