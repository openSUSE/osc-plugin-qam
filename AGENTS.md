# Agent Notes

## Overview
- `osc-plugin-qam` (package `oscqam`) is the **osc plugin** that powers the SUSE QA
  Maintenance review workflow. It adds `osc qam <subcommand>` (`assign`, `approve`,
  `reject`, `comment`, `info`, `list`, `my`, `unassign`, `rmcomment`, `assigned`,
  `version`) on top of osc's request/review API to assign, sign off, and
  approve/reject maintenance requests.
- Two request backends: classic OBS/IBS requests dispatch through `osc`; SLFO
  requests dispatch to **Gitea** pull requests. The plugin recognises which one is
  in play from the request, not from a flag.
- The library lives in `oscqam/`; the user-facing entry points are the thin osc
  plugin wrappers `qam_*.py` installed to `/usr/lib/osc-plugins/`, each mapping to
  one `osc qam <name>`.
- PRs go to GitHub **`openSUSE/osc-plugin-qam`**, default branch **`master`**. The
  package is built in IBS `QA:Maintenance`.

## Setup & Commands
- Setup (matches CI): `uv sync --locked`.
- Make targets:
  - `make typecheck` — `uv run ty check`
  - `make only-test` — `uv run pytest`
  - `make test-with-coverage` — pytest (cov config from pyproject) + xml/junit report + `--cov-fail-under=65` (CI test job)
  - `make checkstyle` — `uv run ruff format --check --diff ./` + `ruff check .`
  - `make tidy` — `uv run ruff format ./` (auto-fix style)
  - `make test` — `only-test` + `checkstyle` + `typecheck` + `docs` (full gate)
  - `make docs` — sphinx-build with -W (used by CI docs job)
- Run as a user does: `osc qam --help` (the plugin must be on osc's plugin path;
  see `Documentation/devel.rst`).

## Testing
- Pytest collects `tests/` (config in `[tool.pytest.ini_options]`). Request/template
  XML fixtures live in `tests/fixtures/*.xml`; osc/HTTP interactions are stubbed in
  the tests, never hitting the network.
- Focus a test: `uv run pytest tests/test_model.py::test_name`.

## Architecture (non-obvious bits)
- `oscqam/actions/` — one `*Action` per operation (`assignaction`, `approveaction` /
  `approveuseraction` / `approvegrpoupaction`, `rejectaction`, the `list*` family,
  …), all subclassing `actions/oscaction.py`. The `oscqam/cli_*.py` modules wire each
  osc subcommand to its action; the `/usr/lib/osc-plugins/qam_*.py` wrappers are the
  osc entry points.
- `oscqam/models/` — domain wrappers over `osc.core`:
  - `request.py` (`Request`): note `src_project_to_rrid` derives the testreport RRID.
    For SLFO **staging** requests the report id comes from the request's **target**
    project (e.g. `SUSE:SLFO:1.1`), not the source project.
  - `template.py` (`Template`): builds the `qam.suse.de/testreports/<rrid>/log`
    machine/human report URLs. A wrong RRID here surfaces as a misleading
    "report not generated yet" on assign/approve.
  - plus `group`, `bug`, `comment`, `reviewer`, `assignment`, `filters`,
    `requestfilters`.
- Report/queue data comes from the QEM dashboard and `qam.suse.de`.

## Type & Style
- Supported Python is **3.13+** (`requires-python = ">=3.13"`); ruff
  `target-version = "py313"`, `line-length = 88`; `ty` is pinned to `python-version =
  "3.13"`. Keep code 3.13-compatible.
- `make checkstyle` is `ruff format --check --diff ./` + `ruff check .`, and CI lints the **whole repo
  including `tests/`** — format and lint `tests/` too. A tests-only formatting miss is the
  most common way to red the pipeline.

## Change Workflow
- **Conventional Commits** are expected (`fix:`, `feat:`, `style:`, `build:`,
  `ci:`, `docs:`…); reference SUSE Bugzilla as `bsc#NNNN` / `boo#NNNN`.
- `ChangeLog.rst` is curated at **release time only** — do **not** add a per-PR
  changelog entry (recent feature/fix PRs do not touch it).
- Merge automation (`.mergify.yml`): an approved PR auto-merges once `base=master`,
  all checks pass (`#check-failure=0`, `#check-pending=0`), history is linear, there
  is `>=1` approval and no changes-requested. Hold a PR from auto-merge with the
  **`not-ready`** (or `acceptance-tests-needed`) label; fast-track with `merge-fast`.

## Definition of Done (hard rules)
- Run the full gate on the **whole repo** (`./`) before pushing or claiming done.
  CI uses separate jobs (lint, typecheck, docs, test with 3.13/3.14 matrix).
  Locally run: `make checkstyle && make typecheck && make docs && make test-with-coverage`
  (or `make test` for the components except the cov-fail-under variant).
  Equivalently:
  `uv run ty check`
  `uv run ruff format --check --diff ./ && uv run ruff check .`
  `uv run --group doc sphinx-build -b html -W --keep-going Documentation Documentation/_build/html`
  `uv run pytest --cov-report=xml --junitxml=junit.xml -o junit_family=legacy --cov-fail-under=65`
- "Done" means CI is **observed** green, not predicted — report status from the
  actual run. Patch coverage is enforced via Codecov.
- Rebase on `upstream/master` and keep history **linear** (mergify requires it).

## External Dependencies
- Driven through `osc` (`osc.core`) for OBS/IBS request/review actions and through the
  Gitea API for SLFO pull requests. Source installs use `uv`, not PyPI.

## Further Reading
- `Documentation/devel.rst` — dev setup, the osc plugin path, and running the tests. (includes release tagging for GH release workflow)
- `README.rst` — user-facing overview and workflows.
- `.mergify.yml` — merge automation rules referenced above.
- `.github/workflows/ci.yml`, `codeql-analysis.yml`, `release.yml` — modernized CI (lint/typecheck/docs/test matrix), CodeQL, and tag-triggered releases (no 'v' prefix).
