# Validity: vendor agnostic configuration compliance
## What is it?
Validity is the NetBox plugin to deal with configuration compliance. You define compliance tests and Validity checks network device configuration files against these tests. As a result you can find out which devices are provisioned properly (according to the tests you have written) and which are not.

To use validity you need:
1. Store configuration files of your devices in a Git repository. Validity does not collect the configs from your network, you have to do it by third-party tool (e.g. [oxidized](https://github.com/ytti/oxidized)).
2. Define [TTP Template](https://ttp.readthedocs.io/en/latest/) to translate the config from vendor specific format into JSON.
3. Write compliance test as a python expression, e.g. `device.config["ntp-servers"] == ["1.2.3.4", "5.6.7.8"]`
4. Apply created test to specific devices and get the results per device (passed or failed).


## Key features
* Writing compliance tests using Python and [JQ](https://stedolan.github.io/jq/manual/) syntaxes
* Flexible selector system to apply tests only for specific subset of devices
* Concept of **dynamic pairs**. With dynamic pair you can compare 2 different devices between each other (e.g. compare configuration of 2 MC-LAG members).
* **Test fail explanation**. When some test fails, you can get the **explanation** of the calculation process step by step.
* **Reports and webhooks**. After execution of some bunch of tests you can get the report with passed/failed statistics grouped by some Location/Site/Manufacturer/etc. Moreover, you can provision the webhook to notify an external system when compliance report is generated.
* **Test extensibility**. You can define your own python functions or classes to reuse the code between multiple compliance tests.
* Possibility to store all heavy text-based entities (like compliance tests or TTP Templates) in a Git repository
