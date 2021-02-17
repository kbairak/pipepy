import os

import pytest

from pipepy import PipePyError, cd, export, jobs, sleep, source, wait_jobs


def pwd():
    return os.path.abspath(os.curdir)


def test_cd():
    original_pwd = pwd()

    cd('src')
    assert pwd() == original_pwd + "/src"
    cd('..')
    assert pwd() == original_pwd

    with cd('src'):
        assert pwd() == original_pwd + "/src"
    assert pwd() == original_pwd

    cd(original_pwd)


def test_export():
    original_path = os.environ['PATH']

    export(PATH=original_path + ":foo")
    assert os.environ['PATH'] == original_path + ":foo"
    export(PATH=original_path)
    assert os.environ['PATH'] == original_path

    with export(PATH=original_path + ":foo"):
        assert os.environ['PATH'] == original_path + ":foo"
    assert os.environ['PATH'] == original_path

    with export(PATH=original_path + ":foo"):
        assert os.environ['PATH'] == original_path + ":foo"
        export(PATH=original_path + ":FOO")
        assert os.environ['PATH'] == original_path + ":FOO"
    assert os.environ['PATH'] == original_path + ":FOO"

    with export(DUMMY_ENV_VAR_____="FOO"):
        assert os.environ['DUMMY_ENV_VAR_____'] == "FOO"
    assert 'DUMMY_ENV_VAR_____' not in os.environ

    os.environ['PATH'] = original_path


def test_jobs():
    command = sleep(.01).delay()
    assert len(jobs()) == 1
    assert jobs()[0]._process.pid == command._process.pid

    command.wait()
    assert len(jobs()) == 0

    command = sleep(.01).delay()
    assert len(jobs()) == 1
    assert jobs()[0]._process.pid == command._process.pid

    wait_jobs()
    assert len(jobs()) == 0


def test_source():
    # Simple
    with cd('src/tests/playground'):
        with source('env'):
            assert os.environ['FOO___'] == "foo"
            assert 'BAR___' not in os.environ
        assert 'FOO___' not in os.environ

        source('env')
        assert os.environ['FOO___'] == "foo"
        assert 'BAR___' not in os.environ
        del os.environ['FOO___']
        assert 'FOO___' not in os.environ

    # Recursive
    with cd('src/tests/playground/envdir'):
        with source('env', recursive=True):
            assert os.environ['FOO___'] == "foo"
            assert os.environ['BAR___'] == "bar"
        assert 'FOO___' not in os.environ
        assert 'BAR___' not in os.environ

        source('env', recursive=True)
        assert os.environ['FOO___'] == "foo"
        assert os.environ['BAR___'] == "bar"
        del os.environ['FOO___']
        assert 'FOO___' not in os.environ
        del os.environ['BAR___']
        assert 'BAR___' not in os.environ

    # Bad file
    with cd('src/tests/playground'):
        prev = dict(os.environ)
        source('bad_env')
        assert prev == dict(os.environ)

        with pytest.raises(PipePyError):
            source('bad_env', quiet=False)

    # Preserves further edits
    with cd('src/tests/playground'):
        with source('env'):
            export(FOO___="FOO")
        assert os.environ['FOO___'] == "FOO"
