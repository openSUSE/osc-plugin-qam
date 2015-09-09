=================
Manager workflows
=================

Manager workflows provide overview over the current update-situation.

List assigned updates
=====================

List all updates assigned to a member of a QAM group.

.. code:: bash

   ibs qam assigned

List unassigned groups for updates
==================================

List all unassigned QAM groups for updates:

.. code:: bash

   ibs qam open -T -F ReviewRequestID -F SRCRPMs -F Rating -F Products -F "Incident Priority" -F "Unassigned Roles"
