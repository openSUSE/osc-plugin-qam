.. image:: https://github.com/openSUSE/osc-plugin-qam/actions/workflows/ci.yml/badge.svg
 :target: https://github.com/openSUSE/osc-plugin-qam/actions/workflows/ci.yml
.. image:: https://codecov.io/gh/openSUSE/osc-plugin-qam/branch/master/graph/badge.svg?token=JJRU27WKZ0 
 :target: https://codecov.io/gh/openSUSE/osc-plugin-qam
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

          zypper ar -f http://download.suse.de/ibs/QA:/Maintenance/<distribution>/QA:Maintenance.repo
          zypper in python-oscqam

Currently supported distributions are:

- Tumbleweed

- Leap 15.x

- SLE 12-SP4+

- SLE 15.x

Usage
-----

After the package is installed a new command is now available for osc: ``osc
qam``.

.. note::

   The plugin is currently only useful for the *internal* buildservice.
   You should actually use your alias that uses ``https://api.suse.de``
   or add the flag ``--apiurl=https://api.suse.de``.

   If you do not want to set an alias, you can configure ``osc`` to
   automatically default to the internal ibs api.
   Update your ``.oscrc`` ``[general]`` section:

   .. code:: bash

      [general]
      apiurl = https://api.suse.de

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

          osc qam
          osc-qam> list

The single command to list open requests:

.. code-block:: bash

          osc qam list
