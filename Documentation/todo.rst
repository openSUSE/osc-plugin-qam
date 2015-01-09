Todo
====

This little section documents known issues or outstanding features requests
that should be addressed in the future:

1. Readline support
-------------------

   Currently not possible for multiple reasons:

   ``osc`` includes an outdated replacement for the ``cmd`` module that breaks
   readline functionality (https://github.com/trentm/cmdln/issues/1).

   .. note::
      This has been fixed in the osc-upstream project on github.
      As soon as a release occurred this part of the problem is solved.

   Moreover ``osc`` replaces the ``stdout`` and ``stderr`` file-descriptor
   with a unicode aware wrapper-object.
   Even when the fixes to the ``cmd`` replacement are made, this wrapper still
   prevents ``readline`` from working.

   .. note::
      It is possible to just replace the wrapper descriptors with the original
      ones to allow readline support.
      However this might lead to problems, as osc probably did not include the
      wrapper object just for fun.

2. openSUSE support
-------------------

   The openSUSE build service uses a different template format that needs some
   adjustments in ``models.py``.

3. Change to server-side unassign
---------------------------------

   As soon as the ``unassign`` action is implemented server-side this logic
   should be used. Once this is changed all the code to best-guess the group
   the user was reviewing for should also be purged from the ``Request``
   class.
