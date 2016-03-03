=================
Manager workflows
=================

Manager workflows provide overview over the current update-situation.

List assigned updates
=====================

List all updates assigned to a member of a QAM group.

.. code:: bash

   ibs qam assigned

If you wish to only see updates that are assigned for a specific group
you can use the '-G' or '--group' flag with the group as argument.

You can also show reviewable updates for multiple groups by passing
the flag more than once.

.. code:: bash

   ibs qam assigned -G 'qam-manager' -G 'qam-sle'

List unassigned groups for updates
==================================

List all unassigned QAM groups for updates:

.. code:: bash

   ibs qam open -T -F ReviewRequestID -F SRCRPMs -F Rating -F Products -F "Incident Priority" -F "Unassigned Roles"
