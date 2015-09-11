PYTHON=python2
PYTEST=py.test-2.7

all:

	$(PYTHON) setup.py build

check:

	$(PYTEST) tests

release:

	bs-update -P QA:Maintenance -d . HEAD
