import os

from pipepy import cd, export


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
