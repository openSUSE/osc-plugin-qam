Installation
============

Overview
--------

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
------------

To install the plugin add the repository for your distribution from here:
http://download.suse.de/ibs/QA:/Maintenance/

.. code:: bash

          zypper ar -f http://download.suse.de/ibs/QA:/Maintenance/ qa_maintenance_tools
          zypper in python-oscqam

Currently supported distributions are:

- openSUSE 13.1
    
- openSUSE 13.2
    
- openSUSE Factory
    
- SLE 12
    
- SLE-11-SP3 (The plugin requires a fairly recent osc-version: use this
    repository
    http://download.opensuse.org/repositories/openSUSE:/Tools/SLE_11_SP3/)

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
session. This is the easier way to see all commands and get help for a
specific command:

.. code:: bash

          ibs qam
          osc-qam> help
          Usage: osc qam [command] [opts] [args]
          
          openSUSE build service command-line tool qam extensions.
          
          commands:
             approve       Approve the request for the user.
             assign        Assign the request to the user.
             help (?, h)   give detailed help on a specific sub-command
             list          Show a list of all open requests currently running. The l...
             man           generates a man page
             quit (q)      Quit the qam-subinterpreter.
             reject        Reject the request for the user.
             unassign      Assign the request to the user.
          
          osc-qam> help approve
          approve: Approve the request for the user.
          
          The command either uses the user that runs the osc command or the user
          that was passed as part of the command via the -u flag.
          
          Usage:
             osc-qam approve REQUEST_ID 
          
          Options:
             -h, --help          show this help message and exit
             -u USER, --user=USER
                                 User to assign for this request.

Instead of running the commands in the interactive session it is also possible
to just write out the complete command following the osc qam part:

The interactive command sequence to list open requests:

.. code:: bash

          ibs qam
          osc-qam> list

The single command to list open requests:

.. code:: bash
          
          ibs qam list
