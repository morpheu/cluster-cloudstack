.PHONY: test

test: deps 
	@python -m unittest discover -v
	@flake8 --max-line-length=110 --exclude=dist,build .
	@coverage

deps:
	pip install -e .[tests]

coverage: deps
	rm -f .coverage
	coverage run --source=. -m unittest discover
	coverage report -m --omit=test\*,run\*.py,build\*,dist\*
