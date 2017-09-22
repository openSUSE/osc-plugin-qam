ChangeLog
#########

0.24.0
======

- Rework of assignment inference.
- Document -G flag for approve to warn about (probably) incorrect usage.

0.23.0
======

- Drop β priority: no longer used - default priority now replaces it completely.

0.22.1
======

- Make logging configurable and store log-files in $XDG_DATA_HOME/oscqam/.
- Fix assignment inference when the expected invariants don't hold.

0.22.0
======

- Fix naming conflict with newer versions of osc used in tumbleweed.


0.21.0
======

- Correctly handle new testreports that have no $Author header anymore.

0.20.1
======

- Report errors when accessing the IBS.
- Removed -U flag from approve. Approval for another user is not possible.

0.20.0
======

- Add new issues field: lists number of issues contained in the request.

0.19.3
======

- Fix crash when url not retrievable.

0.19.2
======

- Fix Assignment inference, when history events out of order.

0.19.1
======

- Fix approval action raising errors if the last qam-group was approved.

0.19.0
======

- Switch to using HTTPS for testreports, as HTTP gives problem through VPN.

0.18.1
======

- Fix bnc#998835: better error message and basic return codes.

0.18.0
======

- Internal refactoring: errors, messages.
- Fix bnc#989567.
- Can now approve for groups directly.
- When approving as a user additional (possible) reviews for the user will be
  pointed out.

0.17.1
======

- Fix bnc#676298.

0.17.0
======

- Add 'creator' field to 'info' and 'assigned' commands.
- Correctly handle 'end of transmission'.

0.16.0
======

- Bugfix: unassign action no longer leaves buildservice in
  inconsistent state if one of the steps can not be completed.
- New alias for quit: 'quit'.
- Will output url to testreport in reject / approve actions' comments.

0.15.3
======

- Fix incorrect formatting of 'Package-Streams' field.
- Fix incorrect formatting of 'Bugs' field.

0.15.2
======

- Provide alternate implementation for SSL connection on python 2.6
  versions: utilizes requests library.

0.15.1
======

- Fix SSL connection to https://maintenance.suse.de

0.15.0
======

- Use beta-priority to order requests instead of normal priority.
- Fallback to normal-priority if beta-priority can not be loaded.
- Rejects no longer proceed if no comment is set, even if a message is
  provided.
- Reject comments will now be prefixed by the plugins [oscqam] prefix.


0.14.1
======

- Fix 'do_my' method: now calls 'do_assigned' with a valid opts.

0.14.0
======

- Can now limit groups shown in 'open'/'assigned' commands via '-G'
  flag.

0.13.1
======

- Fix rejection if a maintenance incident has already (exactly) one
  reject.

0.13.0
======

- Allow > 1 group to be assigned at a time.

0.12.2
======

- Pass correct project to set_attribute call.

0.12.1
======

- Can specify multiple 'reject_reasons'

0.12.0
======

- Added 'reject_reasons' to the rejection-command:
  It is now required to specify *why* a request was rejected.
  The reason will be stored in the corresponding Maintenance Incident.

0.11.0
======

- Added 'my' command to list requests assigned to the current user.
- Changed 'open' command: will no longer lists requests that the user
  is already assigned to.

0.10.1
======

- Fix assign action for OBS.

0.10.0
======

- Add OBS support to the plugin:
  - Commands tested & available: open / assigned / info.
  - Commands untested: assign / unassign / accept / reject.

0.9.0
=====

- Add flag to assign action to not check if a template exists.

0.8.1
=====

- Fix bug when assigning a previously rejected update.

0.8.0
=====

- Add comments features: allow listing and deletion.
- Check previous rejects when assigning tester.

0.7.1
=====

- Add missing dependency to spec-file: python-futures

0.7.0
=====

- Use threading to load requests.
- Memoize build service requests.
- Fix bnc#949745: allow multiline comments.

0.6.0
=====

- Add 'assigned' command to possible commands: list all requests that are
  assigned (as far as the plugin can infer them).
- Add 'info' command to possible commands: list information for one request
  only.
- Inference for assignments now only considers qam-groups and ignore qam-auto.

0.5.2
=====

- Add 'status' and 'Test Plan Reviewer' checks to approve action.
- Fix reject outputting complete log.
- Fix bnc#943294: match 'Test Plan Reviewers' if 'Test Plan Reviewer' is not
  found.
- Fix bnc#942510: print message after assignment was successful.

0.5.1
=====

- Fix bug in list user-assigned command.

0.5.0
=====

- Assign-check: do not allow assign before the template is generated.
- Assign-check: do not allow assign for more than one group.
- Add Python 2.6 backport for total_ordering decorator.

0.4.1
=====

- Rewrote assignment inference logic to handle incorrect case.
- Workaround for OBS2.7 and osc < 0.152 clients that can not handle
  acceptinfo-tags.

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
