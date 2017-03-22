Getting started
===============

Overview
--------

The plugin provides the following new features:

- a new subshell that can be started via ``osc qam`` that only accepts the new
  commands of this plugin.

- it adds command to help with the update workflow.

- to see a list of provided commands use ``osc qam help`` and to see what each
  command does just use ``osc qam help <command>``.

For detailed information about common use cases see the :ref:`workflows`.

Installation
------------

To install the plugin add the repository for your distribution from here:
http://download.suse.de/ibs/QA:/Maintenance/

.. code:: bash

          zypper ar -f http://download.suse.de/ibs/QA:/Maintenance/<distribution> qa_maintenance_tools
          zypper in python-oscqam

Currently supported distributions are:

- Tumbleweed

- Leap 42.{1, 2}

- SLE 12-{SP1, SP2}

Usage
-----

After the package is installed a new command is now available for osc: ``ibs
qam``.

.. note::

   The plugin is currently only useful for the *internal* buildservice, so
   whenever this document uses ``ibs qam``, you should actually use your alias
   that uses ``https://api.suse.de`` or add the flag
   ``--apiurl=https://api.suse.de``.

Running the command without any further arguments will start an interactive
session.

.. note::

   When you are running a older version of ``osc`` (e.g. 0.148) then the
   readline-support is not working out-of-the-box. Please see
   :ref:`workarounds` to see how to still get it working.

Instead of running the commands in the interactive session it is also possible
to just write out the complete command following the osc qam part:

The interactive command sequence to list open requests:

.. code-block:: bash

          ibs qam
          osc-qam> list

The single command to list open requests:

.. code-block:: bash

          ibs qam list
