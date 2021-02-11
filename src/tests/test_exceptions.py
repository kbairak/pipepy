import pytest

from pipepy import PipePyError, false, set_always_raise, true


def test_exceptions():
    result = true()
    result.raise_for_returncode()

    result = false()
    with pytest.raises(PipePyError):
        result.raise_for_returncode()

    with pytest.raises(PipePyError):
        result = false._r()

    set_always_raise(True)

    with pytest.raises(PipePyError):
        result = false()

    result = false._q()

    set_always_raise(False)
