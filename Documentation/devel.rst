Development
===========

Hosting
-------

The plugin is hosted on the internal ``git``-repository:
http://git.suse.de/?p=fbergmann/oscqam.git

Testing
-------

The oscqam plugin uses pytest_ library to run the test. To setup the project
correctly for usage with it, install it using pip:

.. code:: bash

          cd <src_directory_oscqam>
          pip install --user -e .

Now running the tests with ``py.test`` should work:

.. code:: bash

          cd <src_directory_oscqam>
          py.test ./tests


.. _pytest: http://pytest.org/

Release
-------

The current version of the plugin can be installed from the official
QA-Maintenance_ project in the internal build service:
https://build.suse.de/package/show/QA:Maintenance/python-oscqam

The plugin should keep building for at least the supported versions.

.. _qa-maintenance: https://build.suse.de/project/show/QA:Maintenance
