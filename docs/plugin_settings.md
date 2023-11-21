# Plugin Settings


Validity has some settings which could be changed through [PLUGINS_CONFIG](https://docs.netbox.dev/en/stable/plugins/#configure-plugin) variable inside your `configuration.py`.

## Settings
### git_folder

*Default:* `/opt/git_repos/`

*Type:* `str`

This variable should contain the path to folder where git repositories will be stored.

!!! warning
    The contents of the **git_folder** MUST be shared between NetBox **Web app** and the **RQ Worker** (the instance that executes custom scripts).
    For instance, if you use docker to deploy NetBox, a shared **docker volume** MUST be bound to **git_folder**.


### sleep_between_tests

*Default:* `0.0`

*Type:* `float`

The amount of seconds system will wait between executing each Compliance Test.

Compliance Test execution may cause a lot of DB queries, because Compliance Test is dynamic by its nature and the system cannot prefetch all the required instances before the test. If you're realizing that `Run Compliance Tests` script overwhelms your DB with a lot of queries, you can adjust this setting to spread the queries over time.


# result_batch_size

*Default:* `500`

*Type:* `int`

Execution of the Tests and producing Test Results is carried out in batches. As soon as each batch reaches its maximum size (specified via this variable) all the Test Results within a batch will be uploaded into a DB.


### store_reports

*Default:* `5`

*Type:* `int`

How many [Reports](entities/results_and_reports.md#reports) should the system store.

If the system creates a new Report and the overall reports count exceeds *store_reports*, then the oldest exceeding report(s) will be deleted.

!!! note
    Test Results bound to the Report will be deleted with this Report.


### store_last_results

*Default:* `5`

*Type:* `int`

How many [Test Results](entities/results_and_reports.md#test-results) should the system store for each pair of Compliance Test and Device.

[Run Compliance Tests](entities/scripts.md#run-compliance-tests) script checks this setting after creating a new bunch of Test Results. If there are old Test Results that exceed store_last_results for some pair of (Device, Compliance Test), then the script will delete them.

!!! note
    This setting does not influence Test Results bound to a Report. These results can be deleted only together with the Report they are bound to.


## Settings Example

Here is the full example of Validity settings:

```python
# configuration.py

PLUGINS_CONFIG = {
    'validity': {
        'git_folder': '/opt/git/',
        'sleep_between_tests': 0.02,
        'result_batch_size': 300,
        'store_reports': 7,
        'store_last_results': 8,
    },
    # other plugins configuration
}
```
