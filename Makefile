.PHONY: all
all:

.PHONY: only-test
only-test:
	uv run pytest

.PHONY: checkstyle
checkstyle:
	uv run ruff format --check --diff ./
	uv run ruff check .

.PHONY: typecheck
typecheck:
	uv run ty check

.PHONY: tidy
tidy:
	uv run ruff format ./

.PHONY: test-with-coverage
test-with-coverage:
	uv run pytest --cov-report=xml --junitxml=junit.xml -o junit_family=legacy --cov-fail-under=65

.PHONY: docs
docs:
	uv run --group doc sphinx-build -b html -W --keep-going Documentation Documentation/_build/html

.PHONY: test
test: only-test checkstyle typecheck docs
