Role Name
=========

The `manageiq-automate` role allows for users of ManageIQ Automate to modify and add to the Automate Workspace via an Ansible Playbook.
The role includes a module `automate_workspace` which does all the heavy lifting needed to modify or change the Automate Workspace.

Requirements
------------

ManageIQ has to be Gaprindashvili (G Release) or higher.

The role requires and automatically installs the following modules.
1. `manageiq-api-client-python`
2. `requests`
3. `dpath`

The example playbook makes use of the `automate_workspace` module which is also included as part of this role.

Role Variables
--------------

Auto Commit:
    `auto_commit` defaults to `False` in `defaults/main.yml`.
    If set to `True` it will auto commit back to ManageIQ each
    call to a `set_` method in the `automate_workspace` module.

ManageIQ:
    `manageiq` is a dictionary with a set of connection defaults in `defaults/main.yml`.
    Remember to use Ansible Vault for passwords.
    `automate_workspace` is the url including guid to talk to the Automate Workspace.

```
    manageiq:
        api_url: 'http://localhost:3000'
        username: 'admin'
        password: 'password'
        automate_workspace: 'automate_workspaces/1234'
```

Workspace:
    `workspace` instantiated via `tasks/main.yml`.
    The current version of the workspace as it is modified via methods
    in the `automate_workspace` module.

Dependencies
------------

None

Example Playbook
----------------

A verbose example with manual strings passed to each method of the
`manageiq_automate` module

```
- name: Modify the Automate Workspace
  hosts: localhost
  connection: local

  gather_facts: False
  vars:
  - auto_commit: True
  - manageiq:
        api_url: 'http://localhost:3000'
        username: 'admin'
        password: 'password'
        automate_workspace: 'automate_workspaces/1234'

  roles:
  - syncrou.manageiq-automate

  tasks:
    - name: "Check an attribute"
      manageiq_automate:
        workspace: "{{ workspace }}"
        attribute_exists:
          object: "/ManageIQ/System/Request/call_instance"
          attribute: "::miq::parent"

    - name: "Get an attribute"
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_attribute:
          object: "/ManageIQ/System/Request/call_instance"
          attribute: "::miq::parent"

    - name: "Check a state_var"
      manageiq_automate:
        workspace: "{{ workspace }}"
        state_var_exists:
          attribute: "task_id"

    - name: "Get a state_var"
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_state_var:
          attribute: "task_id"

    - name: "Set a State Var"
      manageiq_automate:
        workspace: "{{ workspace }}"
        set_state_var:
          attribute: "job_id"
          value: "xyz"
      register: workspace

    - name: "Check a Method Parameter"
      manageiq_automate:
        workspace: "{{ workspace }}"
        method_parameter_exists:
          parameter: "task_id"

    - name: "Get a Method Parameter"
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_method_parameter:
          parameter: "invoice"

    - name: "Get the full list of Objects"
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_object_names: yes

    - name: "Get the list of Method Parameters"
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_method_parameters: yes
      register: method_params

    - name: "Get the list of State Vars"
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_state_var_names: yes

    - name: "Get the full list of Object Attribute Names"
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_object_attribute_names:
          object: "root"

    - name: "Set an attribute"
      manageiq_automate:
        workspace: "{{ workspace }}"
        set_attribute:
          object: "root"
          attribute: "my_name"
          value:  "jim"
      register: workspace

    - name: "Set attributes"
      manageiq_automate:
        workspace: "{{ workspace }}"
        set_attributes:
          object: "root"
          attributes:
            family_name: "timmer"
            eldest_son: "reed"
            youngest_son: "olaf"
      register: workspace

    - name: Grab a vmdb object
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_vmdb_object:
          object: root
          attribute: miq_group

```

An example making use of variable substitution to modify some object
attributes with passed in `method_parameters` and change the retry.

```
- name: Siphon Method Parameters into an object
  hosts: localhost
  connection: local
  vars:
  - auto_commit: True
  - object: root
  - interval: 600
  - manageiq:
        api_url: 'http://localhost:3000'
        username: 'admin'
        password: 'password'
        automate_workspace: 'automate_workspaces/1234'

  gather_facts: False
  roles:
  - syncrou.manageiq-automate

  tasks:
    - name: "Get the list of Method Parameters"
      manageiq_automate:
        workspace: "{{ workspace }}"
        get_method_parameters: yes
      register: method_params

    - name: "Set attributes"
      manageiq_automate:
        workspace: "{{ workspace }}"
        set_attributes:
          object: "{{ object }}"
          attributes: "{{ method_params.value }}"

    - name: Set Retry
      manageiq_automate:
        workspace: "{{ workspace }}"
        set_retry:
          interval: "{{ interval }}"
```

License
-------

Apache
