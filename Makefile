publish: build
	python -m twine upload dist/*

clean:
	rm -rf build dist

build: clean
	python -m build

test:
	pytest

_covtest:
	pytest --cov=src/pipepy --cov-report=term-missing

covtest: _covtest
	coverage html
	firefox htmlcov/index.html

watchtest:
	pytest-watch

debugtest:
	pytest -s
