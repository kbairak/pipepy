from pipepy import cd, pymake  # Of course we will use pipepy to test pymake


def test_pymake():
    cd('src/tests/playground')
    assert str(pymake.one) == "one\n"
    assert str(pymake.two) == "two\n"
    assert str(pymake.one_and_two) == "one\ntwo\n"
    cd('../../..')
