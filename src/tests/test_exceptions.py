import pytest

import pipepy
from pipepy import PipePyError, false, true


def test_exceptions():
    result = true()
    result.raise_for_returncode()

    result = false()
    with pytest.raises(PipePyError):
        result.raise_for_returncode()

    with pytest.raises(PipePyError):
        result = false._r()

    pipepy.set_always_raise(True)

    with pytest.raises(PipePyError):
        result = false()

    result = false._q()

    pipepy.set_always_raise(False)
