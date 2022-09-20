from pipepy import cat, echo, grep


def test_pipe_command_to_command():
    assert str(echo("aaa\nbbb") | grep("bbb")) == "bbb\n"

    result = echo("aaa\nbbb")()
    assert str(result | grep("bbb")) == "bbb\n"


def test_pipe_command_to_function():
    assert echo("aaa\nbbb") | (
        lambda output: [item.upper() for item in output.split()]
    ) == ["AAA", "BBB"]

    assert echo("aaa\nbbb") | (
        lambda stdout: [line.strip().upper() for line in stdout]
    ) == ["AAA", "BBB"]


def test_pipe_string_to_command():
    str("aaa\nbbb" | grep("b")) == "bbb\n"


def my_input():
    yield "line one\n"
    yield "line two\n"
    yield "line two\n"
    yield "something else\n"
    yield "line three\n"


def my_output(stdout):
    for line in stdout:
        yield line.upper()


def test_long_pipe():
    assert (
        str(my_input() | cat | grep("line") | my_output | grep("TWO")).strip()
        == "LINE TWO\nLINE TWO"
    )


def upperize():
    line = yield
    while True:
        line = yield line.upper()


def test_pipe_to_generator():
    assert list(echo("aaa\nbbb") | upperize()) == ["AAA\n", "BBB\n"]
    assert str(echo("aaa\nbbb") | upperize() | grep("AAA")) == "AAA\n"
