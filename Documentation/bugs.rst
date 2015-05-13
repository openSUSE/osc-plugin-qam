.. _workarounds:

Known bugs & workarounds
========================

This page will list known bugs and (if required) possible workarounds for the
problem.

1. No readline support
----------------------

The fact that the interactive mode is currently not using the
``readline``-module is known and (unfortunately), because of some changes that
``osc`` has made.

To allow ``readline``-like functionality it is possible to use rlwrap_
with the plugin as a current workaround:

After installing rlwrap the following command will restore readline functionality:

.. code-block:: bash

          rlwrap osc --apiurl=https://api.suse.de/ qam

.. _rlwrap: https://github.com/hanslub42/rlwrap
