from pipepy import cd, pymake  # Of course we will use pipepy to test pymake
from pipepy.pymake import _pymake


def test_pymake_simple():
    with cd('src/tests/playground'):
        assert str(pymake.echo1) == "hello world\n"
        _pymake('echo1')  # Run it again, for coverage
        assert str(pymake.echo2) == "hello world\n"
        _pymake('echo2')  # Run it again, for coverage
        assert str(pymake.echo3) == "hello world\nhello world\n"
        _pymake('echo3')  # Run it again, for coverage


def test_pymake_args():
    with cd('src/tests/playground'):
        assert str(pymake.echo1('msg1=Bill')) == "hello Bill\n"
        _pymake('echo1', "msg1=Bill")  # Run it again, for coverage
        assert str(pymake.echo2('msg2=Mary')) == "hello Mary\n"
        _pymake('echo2', "msg2=Mary")  # Run it again, for coverage
        assert (str(pymake.echo3('msg1=Bill', 'msg2=Mary')) ==
                "hello Bill\nhello Mary\n")
        _pymake('echo3', "msg1=Bill", "msg2=Mary")


def test_pymake_default_target():
    with cd('src/tests/playground'):
        assert str(pymake) == "hello world\n"
        _pymake()
        assert str(pymake('msg1=Bill')) == "hello Bill\n"
        _pymake("msg1=Bill")


def test_pymake_dependencies():
    with cd('src/tests/playground'):
        assert str(pymake.echo4('msg1=Bill')) == "hello Bill\nhello world\n"
        _pymake('echo4', "msg1=Bill")
