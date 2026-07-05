Development
===========

Hosting
-------

The plugin is hosted on our internal ``gitlab`` instance:
https://gitlab.suse.de/qa-maintenance/qam-oscplugin

Working from source
-------------------

After checking out the source code it is required to setup the plugin, so
``osc`` can find and use it.

By default ``osc`` will look in the following paths for plugins:

- ``/usr/lib/osc-plugins``

- ``/usr/local/lib/osc-plugins``

- ``/var/lib/osc-plugins``

- ``~/.osc-plugins``

To make ``oscqam`` available to ``osc`` the start-up point needs to be
available in one of these paths and the modules from oscqam need to be
importable.

An easy way is to symlink the ``oscqam`` folder and ``cli.py`` file into
e.g. ``~/.osc-plugins`` and set the ``PYTHONPATH`` to include this folder:

.. note::

   To make usage of the ``development`` version easier, while also having a
   version from the repository installed, it makes sense to add the
   ``PYTHONPATH`` change to your ``.{bash,zsh}rc``.  To return to the
   installed version just remove the symbolic links.

.. code-block:: bash

                git clone gitlab@gitlab.suse.de:qa-maintenance/qam-oscplugin.git
                ln -s "$PWD/oscqam/cli.py" ~/.osc-plugins/oscqam/cli.py
                ln -s "$PWD/oscqam/oscqam" ~/.osc-plugin/oscqam
                export PYTHONPATH="~/.osc-plugins:$PYTHONPATH"

Testing
-------

The oscqam plugin uses pytest_ library to run the test. To setup the project
correctly for usage with it, install it using pip:

.. code-block:: bash

          cd <src_directory_oscqam>
          pip install --user -e .

Now running the tests with ``py.test`` should work:

.. code-block:: bash

          cd <src_directory_oscqam>
          py.test ./tests


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

Using a virtual environment
---------------------------

To process to setup a virtual environment for the plugin is a little more
involved than or other projects due to dependencies of `osc`.

The process is as follows:

- Install development headers for `python`, `openssl` and `libcurl`:

.. code:: bash

   sudo zypper in python-devel openssl-devel libcurl-devel

- Create the virtualenvironment and switch to it.

- Install the dependencies for `osc`: when installing `pycurl` make sure to set
  `PYCURL_SSL_LIBRARY=openssl` otherwise the installation of `urlgrabber` will
  fail.

.. code:: bash

   pip install pycurl urlgrabber

- Install the osc version referenced by this repository:

.. code:: bash

   git submodule init

   git submodule update

   pip install ./osc

- Install this project into the virtualenvironment:

.. code:: bash

   pip install -e .

Bug reporting
-------------

Bugs can be reported using `bugzilla`_: set the product to ``SUSE Tools`` and
choose the component ``oscqam``.

.. _bugzilla: https://bugzilla.suse.com
