# Name Sets

Name Sets is the method of creating some arbitrary Python functions or classes to later use them in Compliance Tests. Name Sets also can be used to inject some Python standard library functions into test expressions.

One of the common approaches is to move complex expression from tests into a nameset function with appropriate name.
Consider this serialized config:
```yaml
protocols:
  spanning-tree:
    interfaces:
      - name: ge1/0/1
        enabled: true
        priority: 100

      - name: ge1/0/2
        enabled: false
        priority: 100

        # and so on...
```

Let's suppose that we want to check STP is enabled only on interfaces 25 - 28 and disabled on all the others. Let's also suppose that we have multiple slightly different switches and the same interface on them might be named `fa1/0/1`, `ge1/0/1` or `FastEthernet1/0/1`.
This JQ expression extracts all interface name numbers (e.g. "1/0/1") with enabled STP:

`.protocols."spanning-tree".interfaces | map(select(.enabled==true).name | scan("[0-9/]+"))`

And the overall test:

```python
set(
  jq.all(
      '.protocols."spanning-tree".interfaces | map(select(.enabled==true).name | scan("[0-9/]+"))',
      device.config
  )
) == {"1/0/25", "1/0/26", "1/0/27", "1/0/28"}
```
We may move complex JQ expression into a nameset function and then use this function inside the test

**Name Set:**
```python
def stp_enabled_interfaces(device):
    jq_expression = (
      '.protocols."spanning-tree".interfaces'
      ' | map(select(.enabled==true).name | scan("[0-9/]+"))'
    )
    return set(jq.all(jq_expression, device.config))
```

**Test**:
```python
stp_enabled_interfaces(device) == {"1/0/25", "1/0/26", "1/0/27", "1/0/28"}
```

## Name Sets syntax

Name Set is just a piece of Python code which may contain 4 types of statements on the top level:

* `def func(arg1, arg2):` - function definition
* `class MyClass:` - class definition
* `from collections import Counter` - from-import statement
* `__all__ = ["func", "MyClass", "Counter"]` - definition of `__all__` variable containing all the names that should be taken from this Name Set

The entities that are not listed in the `__all__` variable cannot be used in the test expression.

You can use any Python syntax inside the functions/classes you create. These contents are not restricted or analyzed by Validity.

!!! Warning
    The contents of nameset functions/classes are not restricted in any way, so a user can execute arbitrary code inside them.

    **Be very careful with the permissions for adding/modifying Name Sets**. Give the permissions only to administrators or users you completely trust.

    If this is still unacceptable level or risk for you, you can do not use Name Sets at all by revoking the permissions to add/modify them from all the users.

## Fields

#### Name
The Name of the Name Set. Must be unique.

#### Description
Description is mandatory.

#### Global
This boolean field manages the scope of the Name Set. If global is True, then Name Set definitions will be available in every Test inside Validity.

#### Tests
As an alternative of global this field allows you to bind this Name Set to a specific set of Tests.

#### Definitions
Inside this field at the Name Set page you can view your functions/classes defined either via DB or via Git.

At the add/edit form this field is used to store the definitions code inside the DB.
This option fits well when you want to quickly check your Name Set or just don't want to make things complex with Git.

#### Data Source and Data File

!!! info
    You can use only one option per one Name Set instance: you either store your definitions in the DB (Definitions field) or via Data Source. You can't use both approaches at the same time for the same Name Set.

This pair of fields allows you to store definitions as a file in a Data Source (likely pointing to git repository).

This is the best option if you have plenty of complex Name Sets and want to get all the benefits from storing them under version control.
