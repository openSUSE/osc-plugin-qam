Development
===========

Hosting
-------

The plugin is hosted on GitHub:
https://github.com/openSUSE/osc-plugin-qam (default branch ``master``).

Working from source
-------------------

Clone the repository and install the project's dependencies with uv_ (this
matches CI):

.. code-block:: bash

          git clone https://github.com/openSUSE/osc-plugin-qam.git
          cd osc-plugin-qam
          uv sync --locked

To run the plugin the way a user does, ``osc`` needs to discover it on its
plugin path. By default ``osc`` scans the following directories for modules
defining ``OscCommand`` subclasses:

- ``/usr/lib/osc-plugins``

- ``/usr/local/lib/osc-plugins``

- ``/var/lib/osc-plugins``

- ``~/.osc-plugins``

Make the ``oscqam`` package and the ``cli.py`` entry point importable from one
of these paths (for example by symlinking them into ``~/.osc-plugins``), then
run ``osc qam --help``.

Testing
-------

The oscqam plugin uses pytest_ to run the tests, driven through the project's
``make`` targets:

.. code-block:: bash

          make only-test          # uv run pytest
          make test-with-coverage # pytest with coverage + reports
          make checkstyle         # ruff format --check + ruff check
          make typecheck          # ty check
          make docs               # sphinx-build -W
          make test               # only-test + checkstyle + typecheck + docs

To focus a single test:

.. code-block:: bash

          uv run pytest tests/test_model.py::test_name


.. _uv: https://docs.astral.sh/uv/
.. _pytest: http://pytest.org/

Release
-------

The current version of the plugin can be installed from the official
`QA-Maintenance project`_ in the internal build service:
https://build.suse.de/package/show/QA:Maintenance/python-oscqam

The plugin should keep building for at least the supported versions.

.. _QA-Maintenance project: https://build.suse.de/project/show/QA:Maintenance

Procedure
#########

1. Bump ``__version__`` in ``oscqam/__init__.py`` and curate ``ChangeLog.rst``
2. Commit the changes
3. ``git tag <version>`` (e.g. ``1.2.1`` — no ``v`` prefix, to match repose and trigger the release workflow)
4. ``git push && git push <remote> refs/tags/<version>``

Creating a matching version tag will automatically trigger the GitHub release workflow (see ``.github/workflows/release.yml``), which verifies the version, builds sdist+wheel with ``uv build``, and creates a GitHub Release with the artifacts attached (using ``gh release create``).

Note: the RPM package itself is still built and released via the internal IBS in ``QA:Maintenance`` (python-oscqam).

Virtual environment
-------------------

``uv sync --locked`` creates and manages a project-local virtual environment
under ``.venv`` containing ``osc`` and every other dependency. Prefix commands
with ``uv run`` (as the ``make`` targets do) to execute them inside it, or run
``uv run osc qam --help`` to exercise the plugin from the checkout.

Bug reporting
-------------

Bugs can be reported using `bugzilla`_: set the product to ``SUSE Tools`` and
choose the component ``oscqam``.

.. _bugzilla: https://bugzilla.suse.com
