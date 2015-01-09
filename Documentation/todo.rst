Todo
====

This little section documents known issues or outstanding features requests
that should be addressed in the future:

1. Readline support
-------------------

   Currently not possible for multiple reasons:

   ``osc`` includes an outdated replacement for the ``cmd`` module that breaks
   readline functionality (https://github.com/trentm/cmdln/issues/1).

   Moreover ``osc`` replaces the ``stdout`` and ``stderr`` file-descriptor
   with a unicode aware wrapper-object.
   Even when the fixes to the ``cmd`` replacement are made, this wrapper still
   prevents ``readline`` from working.
   
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
