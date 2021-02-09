publish: build
	python -m twine upload dist/*

clean:
	rm -rf build dist

build: clean
	python -m build
