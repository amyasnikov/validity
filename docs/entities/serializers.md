# Config Serializers

Config Serializer is used to translate/parse device configuration from vendor specific format into JSON.

The main approach used in Validity is [Template Text Parser (TTP)](https://ttp.readthedocs.io/en/latest/Overview.html). This library allows you to define text template and then parse the configs according to that template. Template language is very simple and looks like Jinja2 in the reverse way.

There is another one way: you can somehow get JSON config from plain config by yourself, store it in Git Repository and say Validity to read the file as already prepared JSON or YAML. This can be useful for some network vendors which have their own tools for getting JSON-formatted config (e.g. `| display json` on Junos).

## Fields

#### Name

The name of the serializer. Must be unique.

#### Config Extraction Method

The field with the following choices: **TTP** and **YAML**

!!! note
    Remember that YAML is the superset of JSON. So, YAML serializer can be used to read any JSON file.

This field defines the way of getting serialized config from the text.

**TTP** choice requires defining a template (see the other fields below).

**YAML** serializer has no additional properties and may be used to read already prepared JSON or YAML file.


#### TTP Template

Inside this field at the serializer page you can view your template defined either via DB or via Git.

At the add/edit form this field is used to store TTP Template inside the DB.
This option fits well when you have small templates or just need to quickly test some setup.


#### Git Repository and File Path

!!! info
    You can use only one option per one serializer instance: you either define your template via DB (TTP Template field) or via Git (Git Repository and File Path fields). You can't use both approaches at the same time.

This pair of fields allows you to define the template as a file in the Git repository.

This is the best option if you have large complex templates and want to get all the benefits from storing them under version control.


## Bind serializers to devices

There are 3 ways to bind a serializer to device:

* Set the serializer at **Manufacturer** level. Go to Manufacturer page at set the serializer via custom fields. This action applies this serializer to all the devices with this Manufacturer.

* Set the serializer at **Device Type** level. Go to Device Type page at set the serializer via custom fields. This action applies this serializer to all the devices with this Device Type and overwrites the value from Manufacturer.

* Set the serializer at the individual **Device** level. Go to Device page at set the serializer via custom fields. This action applies this serializer to one specific device and overwrites the values from Device Type and Manufacturer.

When device has bound serializer and repository you can find out how serialized config looks like at the Device page (**Serialized Config** tab) or by using API handle `/api/plugins/validity/devices/<id>/serialized_config/`
