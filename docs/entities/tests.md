# Compliance Tests

Tests are the main thing Validity was created for.

In general, Tests are Python expressions that are bound to [Selectors](selectors.md). Inside test expression you can use:

* Python built-ins like `str()`, `round()`, `map()` and so on
* `device` variable. This variable represents NetBox `Device` instance plus 2 additional properties: `config` and `dynamic_pair`
* `jq(expression, object)` function. This function allows you to use the full power of [JQ](https://stedolan.github.io/jq/manual/) expressions
* additional functions and classes from bound [Name Sets](namesets.md)


## Test Expressions

You can create tests using **Python expression** syntax. It means that you can't write random python code inside the test, the code you've written must form an expression.

Some examples:

| **Expression**               | **NOT an expression**         |
|------------------------------|-------------------------------|
| `a == 10 + 20`               | `a = 10 + 20`                 |
| `[i * 2 for i in range(5)]`    | `for i in range(5): print(i)` |
| `'ODD' if x % 2 else 'EVEN'` | `if x % 2: res = 'ODD'`       |

If you're still unsure, you always can use python built-in function `eval()` to check your expression. `eval()` works with expressions only and raises `SyntaxError` on all other syntax.

!!! note
    Your expression SHOULD return boolean value as a result. If it don't, the result will be converted to boolean using Python built-in function `bool()`


## Expressions Context

#### built-ins

The most of the Python built-ins are available inside the expression.

Introspection or other possibly dangerous functions like `type()`, `dir()`, `open()`, `eval()` are disabled.

You can find the full list of available built-ins in [this source file](https://github.com/amyasnikov/validity/blob/master/validity/config_compliance/eval/default_nameset.py).


#### jq

```python
jq(expression: str, object: dict | list | str) -> list
```

This function applies `expression` to `object` and return the list of results.

If you want to get only the first result (e.g. your expression produces only one result), you may use

```python
jq.first(expression: str, object: dict | list | str) -> Any
```

#### device

This is the representation of the current device the test is running against. The instance of NetBox `Device` model

**device.config** - the serialized config of the device

**device.dynamic_pair** - dynamic pair for this device, it is also `Device` instance. May be equal to `None` if 

Device has multiple built-in fields and methods that can be used in test expressions.

It's not the purpose of Validity to list all these attributes. If you want you can discover them by yourself using django shell.

```
cd netbox_folder/netbox
./manage.py shell

from dcim.models import Device
device = Device.objects.first()
dir(device)
```

This is how you can discover the whole list of device fields and methods.


#### Expression restrictions

In test expressions you **CANNOT USE**:

* the fields or methods that start with underscore (e.g. `device._meta`)
* `.delete()`, `.save()`, `.update()`, `.bulk_update()`, `.bulk_create()`, `.mro()`, `.format()`, `.format_map()` methods
* introspection or other dangerous built-ins like `type()`, `open()` or `eval()`
* Creation of very long strings (over 1&nbsp;000&nbsp;000 characters) or very long comprehensions (over 100&nbsp;000 items)

!!! Warning
    As you may notice, execution of the test with the above defaults is **RELATIVELY** safe. It means that you can't break anything with some obvious way. However:
    
    * The users can bring their own functions into the tests via Name Sets. No one besides the author can guarantee that these functions are safe
    * it's still random code execution and no one can guarantee that it is safe

    **So, you must assign the permissions to add/modify the tests with cautions.**


## Fields

#### Name
The name of the test. Must be unique.

#### Severity
One of the `LOW`, `MIDDLE` or `HIGH`. This param influences the future analysis of the [Test Results](results_and_reports.md#test-results) and the appearance of [Reports](results_and_reports.md#reports) (test results inside the report will be grouped by test severity).

#### Selectors
The list of selectors this test is bound to.

#### Description
Description of the test is mandatory. Writing the meaningful description for each of your tests may facilitate the future usage/modification of this test and is considered a best practice.

#### Expression
Inside this field at the test page you can view your expression defined either via DB or via Git.

At the add/edit form this field is used to store an expression code inside the DB.
This option fits well when you want to quickly check your test or just don't want to make things complex with Git.

#### Git Repository and File Path

!!! info
    You can use only one option per one test instance: you either define your expression via DB (Expression field) or via Git (Git Repository and File Path fields). You can't use both approaches at the same time for the same test.

This pair of fields allows you to define the expression as a file in the Git repository.

This is the best option if you have plenty of complex tests and want to get all the benefits from storing them under version control.
