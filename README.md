<div align="center">
    <a href="https://validity.readthedocs.io"><img src="https://raw.githubusercontent.com/amyasnikov/validity/master/docs/images/validity_logo.png" alt="Click to view Validity docs"/></a>
    <h1>Validity: vendor-agnostic configuration compliance</h1>
    <p>
        <img src="https://github.com/amyasnikov/validity/actions/workflows/ci.yml/badge.svg" alt="CI">
        <img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/amyasnikov/9e518ae8babd18b7edd8ee5aad58146b/raw/cov.json" alt="Coverage">
        <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python version">
        <img src="https://img.shields.io/badge/NetBox-3.5|3.6|3.7-blue.svg" alt="NetBox version">
    </p>
</div>

<!--mkdocs-start-->
## What?
Validity is the [NetBox](https://netbox.dev) plugin to write "auto tests" for your network devices. You define compliance tests and Validity checks device state or configuration against these tests. The two most obvious use cases for such a functionality include:

* **Configuration compliance**. You can make sure your devices are provisioned properly, and their config follows the rules you have defined via tests.
* **Pre- / post-configuration checks**. You can make sure your network is in the expected state before or/and after configuration changes have been made. You can use Validity API to include these checks into your automation pipelines.

**Validity usage workflow:**

1. Gather state/config of your devices. Pull it from Git repository or poll the devices directly.

2. Define [serialization method](https://validity.readthedocs.io/en/latest/entities/serializers/) (the way to translate your raw data into JSON-like structure).

3. Write compliance test as a Python expression, e.g.<br/>
`device.config["ntp-servers"] == ["1.2.3.4", "5.6.7.8"]`<br/>
or<br/>
`device.state.sh_ospf_neighbors["10.1.1.1"]["state"] == "Up"`

4. Apply created test to specific devices and get the results per device (passed or failed).


## Why?
Validity helps you to concentrate on what really matters - defining the criteria of healthy and valid network and following these criteria.

Validity completely separates compliance test code from all the other things like data collection, parsing and storage. It encourages you to write short, clean and understandable compliance tests together with the mandatory description.


## Key Features
* Truly vendor-agnostic. You can easily integrate any vendor config format using [TTP](https://github.com/dmulyalin/ttp) or a bunch of other [serialization options](https://validity.readthedocs.io/en/latest/entities/serializers/)
* Writing compliance tests using Python expressions and [JQ](https://stedolan.github.io/jq/manual/)
* Gathering configuration or state info directly from the devices via **SSH**, **Telnet**, **Netconf** or **REST API**.
* Flexible selector system to apply the tests only to a specific subset of devices
* Concept of **dynamic pairs**. With dynamic pair you can compare 2 different devices between each other (e.g. compare the configuration of 2 MC-LAG members).
* **Test result explanation**. When some test fails, you can get the **explanation** of the calculation process step by step. It helps to identify the cause of the failure.
* **ORM access** inside the test. You have full access to the **device** properties. For instance, you may leverage [Configuration Contexts](https://docs.netbox.dev/en/stable/features/context-data/) NetBox feature to store your desired configuration and compare it with the config collected from the device.
* **Reports and webhooks**. After execution of some bunch of tests you can get the report with passed/failed statistics grouped by some Location/Site/Manufacturer/etc. Moreover, you can provision the webhook to notify an external system when compliance report is generated.
* **Test extensibility**. You can define your own python functions or classes to reuse the code between multiple compliance tests.
* Possibility to store all heavy text-based entities (like compliance tests or TTP Templates) in a **Git repository**

## Download and Install

You can download Validity via **pip**
```
pip install netbox-validity
```
After that follow the [installation guide](https://validity.readthedocs.io/en/latest/installation/) to correctly add Validity to your NetBox.
<!--mkdocs-end-->

## Documentation
Read the full documentation on [validity.readthedocs.io](https://validity.readthedocs.io)


## Quick Start

A short video about first steps with Validity:

[![Watch the video](https://img.youtube.com/vi/Hs2IUE6rKC4/0.jpg)](https://www.youtube.com/watch?v=QR04rGwMuPQ)


## Contributing

Feel free to ask a [Question](https://github.com/amyasnikov/validity/discussions), report an [Issue](https://github.com/amyasnikov/validity/issues) or even make a [PR](CONTRIBUTING.md). Read more about contribution in the [CONTRIBUTING](CONTRIBUTING.md) guide.

## Screenshots

![Report Per Device](docs/images/screen_report.png)

![Compliance Test](docs/images/screen_test.png)

![Compliance Test Result](docs/images/screen_result.png)

![Device Serialized Configuration](docs/images/screen_config.png)
