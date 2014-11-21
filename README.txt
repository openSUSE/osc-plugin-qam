Overview
========

This package provides the plugin for the _osc tool that adds additional
features to support the QA-Maintenance workflow.

The plugin provides the following new features:

- a new subshell that can be started via ``osc qam`` that only accepts the new
  commands of this plugin.

- the following new commands:

  - list [-u user]: list all open reviews for the given user that need review
    by one of the ``qam-*`` groups.

  - assign [-u user] <request_id>: assign the user to do a review for the
    given request_id. This command will attempt to guess the group the user
    would probably like to a review for.

  - unassign [-u user] <request_id>: unassign the user to do a review for the
    given request_id. This command will attempt to guess the group the user
    wants to unassign himself for.

  - approve [-u user] <request_id>: will approve a started review of the user
    for the given request_id.

  - reject [-u user] <request_id>: will reject a started review of the user
    for the given request_id.


Installation
============

Either install the package with your package manager or use the following pip
command:

Development
===========

The oscqam plugin uses pytest_ library to run the test. To setup the project
correctly for usage with it, install it using pip:

.. code:: bash

          cd <src_directory_oscqam>
          pip install --user -e .

Now running the tests with ``py.test`` should work:

.. code:: bash

          cd <src_directory_oscqam>
          py.test ./tests


_osc: https://github.com/openSUSE/osc
_py.test: http://pytest.org/
