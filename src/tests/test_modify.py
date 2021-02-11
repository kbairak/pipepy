from pipepy import PipePy, git, ls


def test_no_modify():
    assert PipePy('foo')._args == ["foo"]


def test_converts_to_str():
    assert PipePy(3)._args == ["3"]


def test_glob():
    assert (sorted(PipePy('src/tests/playground/globtest*')._args) ==
            sorted(['src/tests/playground/globtest1',
                    'src/tests/playground/globtest2']))


def test_kwargs():
    assert PipePy(key="value")._args == ["--key=value"]
    assert PipePy(key=2)._args == ["--key=2"]
    assert PipePy(key_key="value")._args == ["--key-key=value"]
    assert PipePy(key=True)._args == ["--key"]
    assert PipePy(key=False)._args == ["--no-key"]


def test_kwargs_first():
    assert PipePy(key="value")('a')._args == ["--key=value", "a"]


def test_sub():
    assert (ls - 'l')._args == ["ls", "-l"]
    assert (ls - 'escape')._args == ["ls", "--escape"]


def test_getattr():
    assert git.status._args == ["git", "status"]


def test_modifiers():
    assert not (PipePy('ls')._b)._text

    job = ls._d()
    assert not job._wait
    job.wait()

    ls_stream = PipePy('ls')._s()
    assert ls_stream._stream_stdout
    assert ls_stream._stream_stderr
    assert ls_stream.stdout is None
    assert ls_stream.stderr is None
    assert ls_stream
