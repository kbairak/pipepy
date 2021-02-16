import os

from pipepy import cd, export, jobs, sleep, wait_jobs


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
