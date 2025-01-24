# Plugin Settings


Validity has some settings which can be changed through [PLUGINS_CONFIG](https://docs.netbox.dev/en/stable/plugins/#configure-plugin) variable inside your `configuration.py`.

## Settings

### result_batch_size

*Default:* `500`

*Type:* `int`

Execution of the Tests and producing Test Results is carried out in batches. As soon as each batch reaches its maximum size (specified via this variable) all the Test Results within a batch will be uploaded into a DB.


### store_reports

*Default:* `5`

*Type:* `int`

How many [Reports](../entities/results_and_reports.md#reports) should the system store.

If the system creates a new Report and the overall reports count exceeds *store_reports*, then the oldest exceeding report(s) will be deleted.

!!! note
    Test Results bound to the Report will be deleted as well.


### polling_threads

*Default:* `500`

*Type:* `int`

Validity uses threads to perform device polling. This setting defines the upper limit of these threads number. If you have extremely large amount of devices (e.g. 100 000), you may want to increase this number to speed up the overall polling process.


### custom_queues

*Type:* `dict[str, str]`

This settings defines custom RQ queue names for Validity scripts. It may be useful if you want to move script execution into a separate queue (e.g. handled by separate set of workers)

!!! note
    Default RQ worker serves 3 queues only: `high`, `default` and `low`. You have to reconfigure your RQ worker (or just start another one in parallel) in case of choosing a different queue name.

    For instance, if you have two custom queues `my_q1` and `my_q2` and want a separate worker for them, then the worker has to be started with these queue names as ths parameters:

    `./manage.py rqworker my_q1 my_q2`


Here are the custom queues which may be defined via this setting:

| Queue Name | Description | Default value |
|---|---|---|
| runtests | Queue for Run Tests script | default |
| backup | Queue for backing up individual Backup Points (Back Up button) | default |

!!! warning
    The `runtests_queue` setting is deprecated **since version 3.1**. Use `custom_queues.runtests` instead


### script_timeouts

*Type:* `dict[str, str | int]`

This setting defines the timeouts for RQ jobs started by Validity (e.g. for running the tests). Timeout defines the maximum amount of time some job can run. If a job exceeds the timeout, it gets terminated.

As was mentioned in the [corresponding article](../entities/scripts.md#stages), **Run Tests** encompass 3 stages (split, apply, combine) where each stage has its own timeout.

| Timeout          | Default Value |
|------------------|---------------|
| runtests_split   | 10m           |
| runtests_apply   | 30m           |
| runtests_combine | 10m           |
| backup           | 10m           |


### custom_pollers

*Type:* `list[validity.settings.PollerInfo]`

*Default:* `[]`

This setting allows to connect custom user-defined [Pollers](../entities/pollers.md) to Validity.

Read more about this feature in the [Custom Pollers](../features/custom_pollers.md) article.


### integrations

*Type:* `dict[str, dict]`

*Default:*

```python
{
    'git': {'author': 'netbox-validity', 'email': 'validity@netbox.local'}
    'S3': {'threads': 10}
}
```

This setting is responsible for various integrations with third-party services, mostly for [Config Backup](../features/config_backup.md) feature.

`threads` param is responsible for the level of parallelism (number of threads used) for multiple files uploading to S3.



## Settings Example

!!! note
    The following example does NOT represent the recommended settings.

Here is the full example of Validity settings:

```python
# configuration.py

PLUGINS_CONFIG = {
    'validity': {
        'result_batch_size': 300,
        'store_reports': 7,
        'polling_threads': 100,
        'custom_queues': {"runtests": "runtests_q"}
        'script_timeouts': {
            'runtests_split': '15m',
            'runtests_apply': '1h',
            'runtests_combine': '5m',
        },
    },
    # other plugins configuration
}
```
