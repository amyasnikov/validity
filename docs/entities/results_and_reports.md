# Test Results

Test Results are produced by Validity as a result of [Run Compliance Tests](scripts.md#run-compliance-tests) script execution.

One Test Result represents the execution of one Compliance Test against one Device.

Old Test Results are the subject for auto-deletion. See [Settings](../plugin_settings.md#store_last_results) for details.

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

Report this test is bound to. Compliance test may not be bound to any Report. You can define it at the start of [Run Compliance Tests](scripts.md#run-compliance-tests) using "Create Report" checkmark.

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

Report ties together Test Results generated from one execution of the [Run Compliance Tests](scripts.md#run-compliance-tests) script.

The user may choose either to create a report together with the Test Results during the Run Compliance Tests script execution or no.

At the report page you can observe test result statistics (total and grouped by severity). Moreover, in web GUI you can choose an additional param to group the results by and display the statistics for each group.

Another one feature is webhook generation after creation of the report. It may be useful for Validity integration with some other OSS/BSS/Monitoring systems. Read more: [Webhooks](../features/webhooks.md)

