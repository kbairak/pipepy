publish: build
	python -m twine upload dist/*

clean:
	rm -rf build dist

build: clean
	python -m build

test:
	pytest

covtest:
	pytest --cov=src/pipepy --cov-report=term-missing
	coverage html
	xdg-open htmlcov/index.html

watchtest:
	pytest-watch

debugtest:
	pytest -s
