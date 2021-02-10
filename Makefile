test:
	pytest

covtest:
	pytest --cov=src/pipepy --cov-report=term-missing

covtest_and_show: covtest
	coverage html
	firefox htmlcov/index.html

watchtest:
	pytest-watch

debugtest:
	pytest -s

checks:
	flake8
	isort

clean:
	rm -rf build dist

build: clean
	python -m build

publish: build
	python -m twine upload dist/*
