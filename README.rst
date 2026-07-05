.. image:: https://github.com/openSUSE/osc-plugin-qam/actions/workflows/ci.yml/badge.svg
 :target: https://github.com/openSUSE/osc-plugin-qam/actions/workflows/ci.yml
.. image:: https://codecov.io/gh/openSUSE/osc-plugin-qam/branch/master/graph/badge.svg?token=JJRU27WKZ0 
 :target: https://codecov.io/gh/openSUSE/osc-plugin-qam

Getting started
===============

Overview
--------

The plugin provides the following features:

- a family of ``osc qam <subcommand>`` commands that drive the QA-Maintenance
  review workflow (assigning, signing off, approving and rejecting maintenance
  requests) on top of osc's request/review API.

- helpers to list, filter and inspect the requests that are open, assigned to a
  group, or assigned to you.

- to see the list of provided commands use ``osc qam --help`` and to see what a
  specific command does use ``osc qam <command> --help``.

For detailed information about common use cases see the :ref:`workflows`.

Installation
------------

To install the plugin add the repository for your distribution from here:
http://download.suse.de/ibs/QA:/Maintenance/

.. code:: bash

          zypper ar -f http://download.suse.de/ibs/QA:/Maintenance/<distribution>/QA:Maintenance.repo
          zypper in osc-plugin-qam

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

Every action is a subcommand of ``osc qam``. For example, to list the open
requests:

.. code-block:: bash

          osc qam list

Commands
--------

The plugin adds the following subcommands. Pass ``--help`` to any of them for
the full list of options (e.g. ``osc qam assign --help``).

Listing and inspecting requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``list`` (alias ``open``) — list requests that are open for review. Filter
  with ``-G/--group`` (repeatable) and ``-U/--user``.

- ``assigned`` — list requests that already have assigned reviews. Filter with
  ``-G/--group`` (repeatable) and ``-U/--user``.

- ``my`` — list the requests currently assigned to you (shortcut for
  ``osc qam assigned -U <your-user>``).

- ``info`` — show detailed information for a single ``request_id``.

  All four commands share the display options ``-F/--fields`` (repeatable,
  choose the columns to output), ``-T/--tabular`` (render as an ASCII table),
  and ``-V/--describe-fields`` (print the available fields).

Working with requests
~~~~~~~~~~~~~~~~~~~~~~~

- ``assign`` — assign a request to a user. Options: ``-U/--user``,
  ``-G/--group`` (repeatable), ``--skip-template`` (do not check that a test
  report template exists).

- ``unassign`` — remove an assignment. Options: ``-U/--user``, ``-G/--group``
  (repeatable).

- ``approve`` — sign off / approve a request. Options: ``-G/--group`` (directly
  approve for a group that does not need reviews), ``--skip-template``.

- ``reject`` — reject a request. Options: ``-U/--user``, ``-M/--message``,
  ``-R/--reason`` (repeatable), ``--skip-template``.

Comments
~~~~~~~~

- ``comment`` — add a comment to a request (``comment <request_id> "<text>"``).

- ``deletecomment`` (alias ``rmcomment``) — remove one of your own comments from
  a request.

Miscellaneous
~~~~~~~~~~~~~~

- ``version`` — print the plugin version.

SLFO and staging requests
-------------------------

SLFO requests are handled through the same request/review API as classic
OBS/IBS requests. Two behaviours are specific to them: for staging requests the
test report id (RRID) is derived from the request's **target** project (for
example ``SUSE:SLFO:1.1``) rather than the source project, while PI releases map
a ``SUSE:SLFO:...`` source to ``SUSE:PI:<version>``; and bug collection is
skipped for SLFO requests.
