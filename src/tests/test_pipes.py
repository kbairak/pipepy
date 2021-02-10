from pipepy import echo, grep


def test_pipe_command_to_command():
    assert str(echo("aaa\nbbb") | grep("bbb")) == "bbb\n"

    result = echo("aaa\nbbb")()
    assert str(result | grep("bbb")) == "bbb\n"


def test_pipe_command_to_function():
    assert (echo("aaa\nbbb") | (lambda output: [item.upper()
                                                for item in output.split()]) ==
            ["AAA", "BBB"])

    assert (echo("aaa\nbbb") | (lambda stdout: [line.strip().upper()
                                                for line in stdout]) ==
            ["AAA", "BBB"])


def test_pipe_string_to_command():
    str("aaa\nbbb" | grep('b')) == "bbb\n"
