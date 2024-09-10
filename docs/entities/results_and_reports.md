# Test Results

Test Results are produced by Validity as a result of [Run Tests](scripts.md#run-tests) script execution.

One Test Result represents the execution of one Compliance Test against one Device.

Old Test Results are the subject for auto-deletion. See [Settings](../installation/plugin_settings.md#store_reports) for details.

## Fields

#### ID

Unique numeric ID of the test result

Test Results have no literal identifier (like "name" for the most of other models), so numeric ID is used even in the GUI.

#### Test

Compliance Test Instance this result was originated from

#### Device

Device instance Compliance Test was executed for

#### Dynamic Pair

Device instance which was used as a [Dynamic Pair](../features/dynamic_pairs.md) for the target device

#### Result

Boolean result of the Compliance Test Expression execution. PASSED or FAILED.


#### Report

Report this test is bound to. Compliance test may not be bound to any Report. You can define it at the start of [Run Tests](scripts.md#run-tests) using "Create Report" checkmark.

#### Explanation

This part consists of parts of an original expression and their respective values. In other words, an expression Evaluator breaks the Test Expression into list of individual actions and outputs the intermediary result for each action.

Let's consider an example.

Expression: `10 + 20 * 3 == 70`

For this expression you can get the following explanation:

| **Expression**    | **Result** |
|-------------------|------------|
| 20 * 3            | 60         |
| 10 + 20 * 3       | 70         |
| 10 + 20 * 3 == 70 | True       |


!!! info
    To quite decrease the verbosity the *attribute* operation (object.attrib) was excluded from the explanations.


# Reports

Report ties together Test Results generated from one execution of the [Run Tests](scripts.md#run-tests) script.

At the report page you can observe test result statistics (total and grouped by severity). Moreover, in web GUI you can choose an additional param to group the results by and display the statistics for each group.

Another one feature is webhook generation after creation of the report. It may be useful for Validity integration with some other OSS/BSS/Monitoring systems. Read more: [Webhooks](../features/webhooks.md)


## Per Device Reports

Starting from 1.3.0 per device reports are available. You can access per device reports via **Devices** tab at Report page or via `/api/plugins/validity/reports/{report_id}/devices/` REST API handle.

Per device report can show you compliance result per each device (passed or failed) together with the tests results bound to the device.

**Minimum Severity** filter parameter (or **severity_ge** via API) can exclude test results with severity LOWER that needed from consideration by the report.
