ChangeLog 
#########

0.4.0
=====

- Incident priority added to requests and list-sorting.

0.3.2
=====

- Errors occurring during 'assign' will no longer crash the program.
- Fixed incorrect log_path in 'decline' action crashing the program.
- Fixed unassign action when user passes a group to unassign.
- Reworked tests.

0.3.1
=====

- Tabular output will split lists into multiple lines.

0.3.0
=====

- Default list output is less verbose.
- To obtain original output use verbose (-v flag).
- List output can be generated as a table (-T flag).
- Configure data to output in list command (-C parameter).

0.2.0
=====

- With upstream osc-version it is now possible to use the readline shortcuts.
- Can use complete request_id in plugin now as well:
  e.g. ibs qam assign SUSE:Maintenance:123:45678

0.1.0
=====

- Implementation for basic commands:
  - list, assign, unassign, approve, reject, comment
