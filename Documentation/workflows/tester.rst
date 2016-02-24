================
Tester workflows
================

There are three workflows:

1. `Find and test an update`_

2. `List updates you are currently testing`_

3. `Check comments`_

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

By default the ``assign``-command (as well as the
``unassign``-command) will try to automatically find the group you can
be assigned (or unassigned) for.  This might not work if the plugin
finds more than one possible group: in this case pass the group names
explicitly via the ``-G`` flag (you can pass more than one group by
repeating the flag).

.. code:: bash

   ibs qam assign -G 'qam-atk' -G 'qam-sle' 12345

Unassigning updates
-------------------

When you realize that an update can not be tested or finished by you,
you can unassign yourself.

When you are assigned to multiple groups, using the command without
any ``--group`` flag will unassign *all* groups you are assigned for.

Passing the ``--group`` flag will only unassign the passed groups:

.. code:: bash

   ibs qam unassign -G 'qam-atk' 12345

This will leave you as a reviewer for the groups you did not unassign
for.

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

You have to either provide a ``reason`` using a ``flag``
(``--reason``) or use the interactive UI when rejecting a request.

The possible values of the reason flag can be checked using the help:

.. code:: bash

   ibs qam help reject

   reject: Reject the request for the user.

   The command either uses the configured user or the user passed via
   the `-u` flag.

   Usage:
       osc qam reject REQUEST_ID

   Options:
       -h, --help          show this help message and exit
       -R REASON, --reason=REASON
                           Reason the request was rejected: admin, retracted, build_problem, not_fixed,
                           regression, false_reject, tracking_issue
       -M MESSAGE, --message=MESSAGE
                           Message to use for rejection-comment.
       -U USER, --user=USER
                           User that rejects this request.

A more detailed listing of possible reasons for rejection (including
examples):

1) Administrative

   - more fixes

   - Security overrides Maintenance

2) Retracted request

   - not needed

   - not fixed (and reported by other parties)

   - End of life of the product

3) Build problems

   - problem with the build/release numbers

   - wrong channels/products/architectures

   - missing packages in the build (not in patchinfo!)

4) Tracked issue(s) not fixed

   - bad upstream fix

   - bad back-port

   - incomplete fix

5) Regression

   - run-time regression

   - dependency/installation issue

6) False reject

   - test setup error

   - manager override to release despite findings

7) Incident tracking issues:

   - bad bug list

   - bad CVE list

   - other issues with patchinfo metadata

List updates you are currently testing
======================================

To see which updates are currently being tested by you (or another user), use
the ``assigned`` command with the ``-U`` parameter:

.. code:: bash

   ibs qam assigned -U <user>

To list the updates currently tested by you, a shortcut command is
provided as well: ``my``, which is equivalent to ``ibs qam assigned -U
"$your_username"``

.. code:: bash

   ibs qam my

Check comments
==============

Apart from working with requests the plugin also allows viewing, adding and
removing comments attached to requests.

Add a comment
-------------

To add a comment to a request use the ``comment`` command:

.. code:: bash

   ibs qam comment <request_id> "<comment_message>"

View comments
-------------

It is possible to have comments be part of the output of any command that
allows the use of the ``--fields`` parameter.

Simple add a ``--fields Comments`` field to your desired output.

.. code:: bash

   ibs qam list --fields ReviewRequestID --fields Comments --fields Rating

Delete comments
---------------

To remove a comment you added to a request use the ``deletecomment`` or
``rmcomment`` command with the ``ReviewRequestID`` you want to remove a
comment from.

.. code:: bash

   ibs qam deletecomment <request_id>

The plugin will then list all found comments and you have to input the
comment_id of the comment you want to remove:

.. code:: bash

    CommentID: Message
    ------------------
    11946: OK
    Comment-Id to remove:

In the given example input 11946 to remove the comment.

.. note::

   You can only remove comments that you created yourself.
