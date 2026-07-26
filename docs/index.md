# pipepy

A Python library for invoking and interacting with shell commands.

[![Build](https://github.com/kbairak/pipepy/workflows/Test%20suite/badge.svg)](https://github.com/kbairak/pipepy/actions)

## Why? Comparison with other similar frameworks

1. **[Xonsh](https://xon.sh/)**: Xonsh allows you to combine shell and Python and enables very powerful scripting and interactive sessions. This library does the same to a limited degree. However, Xonsh introduces a new language that is a superset of Python. The main goal of this library that sets it apart is that it is intended to be a pure Python implementation, mainly aimed at scripting.

2. **[sh](https://github.com/amoffat/sh)** and **[pieshell](https://github.com/redhog/pieshell)**: These are much closer to the current library in that they are pure Python implementations. The current library, however, tries to improve on the following aspects:

    - It tries to apply more syntactic sugar to make the invocations feel more like shell invocations.
    - It tries to offer ways to have shell commands interact with python code in powerful and intuitive ways.
