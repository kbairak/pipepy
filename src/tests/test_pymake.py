from pipepy import cd, pymake  # Of course we will use pipepy to test pymake


def test_pymake_simple():
    cd('src/tests/playground')

    assert str(pymake.echo1) == "hello world\n"
    assert str(pymake.echo2) == "hello world\n"
    assert str(pymake.echo3) == "hello world\nhello world\n"

    cd('../../..')


def test_pymake_args():
    cd('src/tests/playground')

    assert str(pymake.echo1('msg1=Bill')) == "hello Bill\n"
    assert str(pymake.echo2('msg2=Mary')) == "hello Mary\n"
    assert (str(pymake.echo3('msg1=Bill', 'msg2=Mary')) ==
            "hello Bill\nhello Mary\n")

    cd('../../..')


def test_pymake_default_target():
    cd('src/tests/playground')

    assert str(pymake) == "hello world\n"
    assert str(pymake('msg1=Bill')) == "hello Bill\n"

    cd('../../..')


def test_pymake_dependencies():
    cd('src/tests/playground')

    assert str(pymake.echo4('msg1=Bill')) == "hello Bill\nhello world\n"

    cd('../../..')
