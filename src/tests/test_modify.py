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
    job = ls.delay()
    assert job._process is not None
    job.wait()

    job = ls(_raise=False)
    assert not job._raise
