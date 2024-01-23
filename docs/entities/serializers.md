# Serializers

Serializer is used to translate/parse device configuration (or other state info) from vendor specific format into JSON.

The main approach used in Validity is [Template Text Parser (TTP)](https://ttp.readthedocs.io/en/latest/Overview.html). This library allows you to define text template and then parse the data according to that template. Template language is very simple and looks like Jinja2 in the reverse way.

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

**ROUTEROS** serializer allows to parse MikroTik RouterOS configuration files. No additional configuration is needed. See below [MikroTik parsing](#mikrotik-parsing)



#### TTP Template

Inside this field at the serializer page you can view your template defined either via DB or via Git.

At the add/edit form this field is used to store TTP Template inside the DB.
This option fits well when you have small templates or just need to quickly test some setup.


#### Data Source and Data File

!!! info
    You can use only one option per one serializer instance: you either define your template via DB (**Template** field) or via Git (**Data Source** and **Data File** fields). You can't use both approaches at the same time.

This pair of fields allows you to store Serializer template as a file in a Data Source (likely pointing to a git repository).

This is the best option if you have plenty of complex Serializers and want to get all the benefits from storing them under version control.


## Bind Serializers to Devices

Binding Serializer to Device is required to be able to serialize device configuration found by **device_config_path**.

!!! note
    You don't need to bind Serializer to Devices if you use direct polling. In this case Serializers bound to [Commands](commands.md) are used.


There are 3 ways to bind a serializer to device:

* Set the serializer at **Manufacturer** level. Go to Manufacturer page at set the serializer via custom fields. This action applies this serializer to all the devices with this Manufacturer.

* Set the serializer at **Device Type** level. Go to Device Type page at set the serializer via custom fields. This action applies this serializer to all the devices with this Device Type and overwrites the value from Manufacturer.

* Set the serializer at the individual **Device** level. Go to Device page at set the serializer via custom fields. This action applies this serializer to one specific device and overwrites the values from Device Type and Manufacturer.


When device has bound Serializer and Data Source you can find out how serialized config looks like at the Device page (**Serialized State** tab) or by using API handle `/api/plugins/validity/devices/<id>/serialized_state/?name=config`


## MikroTik parsing

Validity has an option to parse MikroTik RouterOS config files without TTP. You just need `ROUTEROS` method in serializer settings to do it. Why MikroTik instead of other vendors? There are 2 reasons:

* MikroTik configuration is really difficult to parse with TTP. You have to take into account all possible configurations of each line with/without each of the parameters.
* At the same time, MikroTik configuration has the same structure as JSON may have. So, it's very easy to translate it using simple Python tools.

!!! warning
    Parser works only if the configuration structure strictly follows the one in `/export` command (or in .rsc file).
    
    Things like `/ip address add address=1.2.3.4/24` won't be parsed

Here is the example configuration:

```
/interface ethernet
set [ find default-name=ether1 ] comment="some comment"
/ip pool
add name=pool1 ranges=192.168.1.100-192.168.1.199
add name=pool2 ranges=192.168.2.100-192.168.2.199
/ip service
set www-ssl certificate=some_cert disabled=no
/ipv6 settings
set disable-ipv6=yes max-neighbor-entries=8192
```

And here is the parsing result in YAML:

```yaml
interface:
  ethernet:
    values:
    - comment: some comment
      find_by:
      - key: default-name
        value: ether1
ip:
  pool:
    values:
    - name: pool1
      ranges: 192.168.1.100-192.168.1.199
    - name: pool2
      ranges: 192.168.2.100-192.168.2.199
  service:
    values:
    - certificate: some_cert
      disabled: false
      name: www-ssl
ipv6:
  settings:
    properties:
      disable-ipv6: true
      max-neighbor-entries: 8192
```