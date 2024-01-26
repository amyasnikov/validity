# Custom Scripts

Validity is shipped together with some [Custom Scripts](https://docs.netbox.dev/en/stable/customization/custom-scripts/).

The scripts are available under `Customization > Scripts` GUI menu.

## Run Compliance Tests

This script executes Compliance Tests and creates Test Result instances.

This script also deletes the old Test Results and Reports if they exceed the maximum number from [settings](../plugin_settings.md).

The script may generate a lot of DB queries. To spread the queries over time you can adjust [sleep_between_tests](../plugin_settings.md#sleep_between_tests) setting.

#### Params

| **Param**                   | **API Param** | **Description**                                                   |
|-----------------------------|---------------|-------------------------------------------------------------------|
| Sync Data Sources           | sync_datasources  | Sync all Data Sources which are bound to Devices<br/> participating in the script execution|
| Make Compliance<br/>Report  | make_report   | Create Report together with Test Results                          | 
| Specific Selectors          | selectors     | Run the tests only for a limited number of selectors              |
| Specific Devices            | devices       | Run the tests only for a limited number of devices.               |
| Specific Test Tags          | test_tags     | Run only those tests which have at least one of<br/> the specified tags|
| Explanation Verbosity<br/>Level | explanation_verbosity | **0** - No explanation at all.<br/>**1** - Explanation of the calculation steps<br/>**2** - the same as **1** plus deepdiff value in case of<br/> comparisons|
| Override DataSource         | override_datasource| Ignore Data Sources bound to Devices and use<br/> this one instead. It may be useful if you want to<br/> use **Validity Polling** Data Source just to run some<br/> operational tests only for now.|