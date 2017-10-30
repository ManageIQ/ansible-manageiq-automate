Role Name
=========

The `manageiq-automate` role allows for users of ManageIQ Automate to modify and add to the Automate Workspace via an Ansible Playbook. 
The role includes a module `automate_workspace` which does all the heavy lifting needed to modify or change the Automate Workspace.

Requirements
------------

ManageIQ has to be Gaprindashvili (G Release) or higher.

The role requires the following modules which are installed previous to running plays in the playbook.
1. `manageiq-api-client-python`
2. `requests`
3. `dpath`

The example playbook makes use of the `automate_workspace` module which is also included as part of this role.

Role Variables
--------------

Auto Commit:
    `auto_commit` defaults to `False` in `defaults/main.yml`
    If set to `True` it will auto commit back to ManageIQ each
    call to a `set_` method in the `automate_workspace` module.

Workspace:
    `workspace` instantiated via `tasks/main.yml` 
    The current version of the workspace as it is modified via methods
    in the `automate_workspace` module.

Dependencies
------------

None

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }

License
-------

Apache
