PYTHON=python2
PYTEST=py.test-2.7

all:

	$(PYTHON) setup.py build

check:

	$(PYTEST) tests

release:

	bs-update -P QA:Maintenance -d . HEAD

beta:

	bs-update -P home:bergmannf -d . HEAD

doc:

	rm -f Documentation/modules.rst
	rm -f Documentation/oscqam.rst
	sphinx-apidoc oscqam -o Documentation
	pushd Documentation && make html
