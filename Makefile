.PHONY: all
all:

.PHONY: only-test
only-test:
	python3 -m pytest

.PHONY: checkstyle
checkstyle:
	black --check --diff ./

.PHONY: tidy
tidy:
	black ./

.PHONY: test-with-coverage
test-with-coverage:
	python3 -m pytest -v --cov=./oscqam --cov-report=xml --cov-report=term --junitxml=junit.xml -o junit_family=legacy

.PHONY: test
test: only-test checkstyle
