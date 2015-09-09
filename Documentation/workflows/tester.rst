================
Tester workflows
================

There are two workflows:

1. `Find and test an update`_

2. `List updates you are currently testing`_

Find and test an update
=======================

1. Find a matching update to test.

2. Assign the update.

3. Approve or reject the update depending on the test outcome.

Finding updates
---------------

To find updates you can test, use the ``open`` command:

.. code:: bash

   ibs qam open

.. note::

   The ``open`` command was called ``list`` before version ``0.6.0``.

   Instead of adding more options to ``list`` (e.g. ``list open``, ``list
   assigned``), the command was split into new commands that describe the
   state of the updates that will be output:

   - ``open``: the update requires testing.

   - ``assigned``: the update is already being tested.

   The ``open`` command will list all updates that fulfil (at least) one of
   the following properties:

   1. You are a member of a group that is not yet being reviewed.

   2. You are already reviewing for the request, but the review is not yet
      finished.

Assigning updates
-----------------

To assign an update use the full identifier of a request:

.. code:: bash

   ibs qam assign SUSE:Maintenance:123:12345

Using only the request-id is also possible.

.. note::

   The request-id is the last numerical part of the full identifier:

   ::

      SUSE:Maintenance:<incident_id>:<request_id>

.. code:: bash

   ibs qam assign 12345

By default the ``assign``-command (as well as the ``unassign``-command) will
try to automatically find the group you can be assigned (or unassigned) for.
This might not work if the plugin finds more than one possible group: in this
case pass the group's name explicitly via the ``-G`` flag.

Finishing updates
-----------------

After testing is done either ``approve`` or ``reject`` the update:

Approve
~~~~~~~

.. code:: bash

   ibs qam approve 12345

Make sure to set the following fields in your test report:

.. code:: text

   status: PASSED
   Test Plan Reviewer: <some reviewer>

.. note::

   Reports with an ambiguous status field (``PASSED/FAILED``) or missing the
   required other fields will be rejected by the plugin.

Reject
~~~~~~

.. code:: bash

   ibs qam reject 12345

Make sure to set the following fields in your test report:

.. code:: text

   status: FAILED
   comment: <reason>

List updates you are currently testing
======================================

To see which updates are currently being tested by you (or another user), use
the ``assigned`` command with the ``-U`` parameter:

.. code:: bash

   ibs qam assigned -U <user>
