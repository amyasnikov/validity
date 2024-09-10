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


### runtests_queue

*Default:* `"default"`

*Type:* `str`

RQ queue name for running the tests. May be useful if you want to move tests execution into separate queue (e.g. handled by separate set of workers)


### script_timeouts

*Type:* `dict`

This setting defines the timeouts for RQ jobs started by Validity (e.g. for running the tests). Timeout defines the maximum amount of time some job can run. If a job exceeds the timeout, it gets terminated.

As was mentioned in the [corresponding article](../entities/scripts.md#stages), **Run Tests** encompass 3 stages (split, apply, combine) where each stage has its own timeout.

| Timeout          | Default Value |
|------------------|---------------|
| runtests_split   | 10m           |
| runtests_apply   | 30m           |
| runtests_combine | 10m           |



## Settings Example

Here is the full example of Validity settings:

```python
# configuration.py

PLUGINS_CONFIG = {
    'validity': {
        'result_batch_size': 300,
        'store_reports': 7,
        'polling_threads': 100,
        'runtests_queue': 'validity_tests',
        'script_timeouts': {
            'runtests_split': '15m',
            'runtests_apply': '1h',
            'runtests_combine': '5m',
        },
    },
    # other plugins configuration
}
```
