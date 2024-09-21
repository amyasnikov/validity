# Scripts

**Scripts** is the way Validity executes long-running tasks. Previously Validity used [NetBox Custom Scripts](https://netboxlabs.com/docs/netbox/en/stable/customization/custom-scripts/) feature for this purpose, but since **release 3.0.0** Validity uses [RQ](https://python-rq.org/) directly to execute its long-running jobs (out of habit, still called "scripts").

## Run Tests

This script executes Compliance Tests and creates Report and Test Result instances.

The script also performs a bunch of auxiliary actions such as:

* Related Data Sources Sync (if requested from user)
* Deletion of old Reports and Tests Results (see [store_reports](../installation/plugin_settings.md#store_reports) setting)

!!! note
    Make sure you've added proper permissions to execute RunTests script for your non-superuser account. Running the script requires `validity.run_compliancetest` permission. Such permission can be created via the following pynetbox call:

    ```python
    nb.users.permissions.create(
        name='validity_runtests',
        object_types=["validity.compliancetest"],
        actions=["run"],
    )
    ```

### Parallel Tests Execution

Validity allows splitting Tests Execution between multiple RQ workers. In this case each RQ worker executes its own portion of the work reducing the overall time required to process all amount of Tests.

Tests Execution is divided between multiple workers on a per-device basis. It means that all the Tests for one particular Device will always be executed on one single worker.

For example if you have 100 devices and want to execute the Tests for them on 3 workers in parallel, just choose `workers_num=3`, it will lead to two of the workers serving 33 devices each and the last one serving 34.

!!! note
    It's the responsibility of NetBox administrator to spawn multiple RQ workers. In most of the deployments there is only one worker by default.


### Execution Params

| **Param**                   | **API Param** | **Description**                                                   |
|-----------------------------|---------------|-------------------------------------------------------------------|
| Sync Data Sources           | sync_datasources  | Sync all Data Sources which are bound to Devices participating in the script execution|
| Specific Selectors          | selectors     | Run the tests only for a limited number of selectors              |
| Specific Devices            | devices       | Run the tests only for a limited number of devices.               |
| Specific Test Tags          | test_tags     | Run only those tests which have at least one of the specified tags|
| Explanation Verbosity Level | explanation_verbosity | **0** - No explanation at all.**1** - Explanation of the calculation steps**2** - the same as **1** plus deepdiff value in case of comparisons|
| Number of Workers           | workers_num   | Number of RQ workers to split test execution between them         |
| Override DataSource         | overriding_datasource| Ignore Data Sources bound to Devices and use this one instead. It may be useful if you want to use **Validity Polling** Data Source just to run some operational tests only for now.|


### Stages
Internally Run Tests script has 3 stages:

* **split**: synchronizes Data Sources (if requested by user) and splits test execution into splices
* **apply**: Executes portion of tests assigned to it at split stage and saves the results to database.  Only this stage can be executed on multiple workers in parallel
* **combine**: collects the overall statistics, fires webhook (if configured)

Each stage has its own timeout which can be adjusted in [Plugin Settings](../installation/plugin_settings.md#script_timeouts)
