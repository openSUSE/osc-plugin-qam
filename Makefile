.PHONY: all
all:

.PHONY: only-test
only-test:
	uv run pytest

.PHONY: checkstyle
checkstyle:
	uv run ruff format --check --diff ./

.PHONY: typecheck
typecheck:
	uv run ty check

.PHONY: tidy
tidy:
	uv run ruff format ./

.PHONY: test-with-coverage
test-with-coverage:
	uv run pytest -v --cov=./oscqam --cov-report=xml --cov-report=term --junitxml=junit.xml -o junit_family=legacy

.PHONY: test
test: only-test checkstyle
