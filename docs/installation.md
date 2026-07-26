# Installation and testing

## Install

```sh
python -m pip install pipepy
```

Or, if you want to modify the code while trying it out:

```sh
git clone https://github.com/kbairak/pipepy
cd pipepy
python -m pip install -e .
```

## Testing

```sh
python -m pip install -r test_requirements.txt

pymake test
# or
pytest
```

There are a few more `pymake` targets to assist with testing during development:

- `covtest` — Produces and opens a coverage report
- `watchtest` — Listens for changes in the source code files and reruns the tests automatically
- `debugtest` — Runs the tests without capturing their output so that you can insert a debug statement

_`pymake` is a console script that is part of `pipepy` that aims to be a replacement for GNU `make`, with the difference that the `Makefile`s are written in Python. More on this [here](pymake.md)._
