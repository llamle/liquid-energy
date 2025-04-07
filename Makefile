.PHONY: clean clean-test clean-pyc test test-cov lint install

clean: clean-pyc clean-test ## remove all build and test artifacts

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr html_cov/

test: ## run tests quickly with the default Python
	pytest

test-cov: ## run tests with coverage report
	pytest --cov=src --cov-report=term --cov-report=html

lint: ## check style with flake8
	flake8 src tests

install: ## install the package to the active Python's site-packages
	pip install -e .
