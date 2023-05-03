# Custom Scripts

Validity is shipped together with some [Custom Scripts](https://docs.netbox.dev/en/stable/customization/custom-scripts/).

The scripts are available under `Other > Scripts` GUI menu.

!!! note
    If you don't see Validity scripts under `Other > Scripts`, please check the [installation](../installation.md) steps related to custom scripts.

## Sync Git Repositories

This is the script to pull the changes from remote Git repository into a local copy.

The local copy is then used to display serialized configs and leverage the entities defined through git files (Tests, Name Sets, Serializers).

You can run this script for an individual Git Repository via `Sync` button at the Repository web page.

#### Params

| **Param**    | **Description**                         |
|--------------|-----------------------------------------|
| Repositories | Specific list of repositories to update |


## Run Compliance Tests

This script executes Compliance Tests and creates Test Result instances.

This script also deletes the old Test Results and Reports if they exceed the maximum number from [settings](../plugin_settings.md).

The script may generate a lot of DB queries. To spread the queries over time you can adjust [sleep_between_tests](../plugin_settings.md#sleep_between_tests) setting.

#### Params

| **Param**              | **API Param** | **Description**                                              |
|------------------------|---------------|--------------------------------------------------------------|
| Sync Repositories      | repositories  | Update all Git Repositories before the run                   |
| Make Compliance Report | make_report   | Create Report together with Test Results                     | 
| Specific selectors     | selectors     | Run the tests only for a limited number of selectors         |
| Specific devices       | devices       | Run the tests only for a limited number of devices.          |
