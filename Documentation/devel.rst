Development
===========

Hosting
-------

The plugin is hosted on the internal ``git``-repository:
http://git.suse.de/?p=fbergmann/oscqam.git

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

.. code-block:: bash
                
                git clone git@git.suse.de:fbergmann/oscqam.git oscqam
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
