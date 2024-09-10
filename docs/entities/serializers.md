# Serializers

Serializer is used to translate/parse device configuration (or other state data) from vendor specific format into JSON-like structure.

Validity has a bunch of different approaches (extraction methods) to accomplish this task.

## Extraction Methods

### TTP

[Template Text Parser (TTP)](https://ttp.readthedocs.io/en/latest/Overview.html) is the preferred approach for parsing vendor-specific configuration data. TTP allows you to define a template and then parse text data according to that template. Template language is very simple and looks like Jinja2 in the reverse way.

**Input data:**
```plain
interface Loopback0
 ip address 10.0.0.1 255.255.255.255
!
interface Vlan100
 ip address 10.100.0.254 255.255.255.0
!
```

**Template:**
```plain
<group name="interfaces">
interface {{ interface }}
 ip address {{ address }} {{ mask }}
</group>
```

**Result:**
```json
{
  "interfaces": [
    {
      "interface": "Loopback0",
      "address": "10.0.0.1",
      "mask": "255.255.255.255"
    },
    {
      "interface": "Vlan100",
      "address": "10.100.0.254",
      "mask": "255.255.255.0"
    }
  ]
}
```

### TEXTFSM

[TextFSM](https://github.com/google/textfsm) is more suitable for `show`-commands output parsing. Unlike vanilla TextFSM, this extraction method outputs list of dicts.

**Input data:**
```plain
Interface                  IP-Address      OK? Method Status                Protocol
FastEthernet0/0            15.0.15.1       YES manual up                    up
Loopback0                  10.1.1.1        YES manual up                    up
```

**Template:**
```plain
Value INTF (\S+)
Value ADDR (\S+)
Value STATUS (up|down|)
Value PROTO (up|down)

Start
  ^${INTF}\s+${ADDR}\s+\w+\s+\w+\s+${STATUS}\s+${PROTO} -> Record
```

**Result:**
```json
[
  {
    "INTF": "FastEthernet0/0",
    "ADDR": "15.0.15.1",
    "STATUS": "up",
    "PROTO": "up"
  },
  {
    "INTF": "Loopback0",
    "ADDR": "10.1.1.1",
    "STATUS": "up",
    "PROTO": "up"
  }
]
```

### ROUTEROS

Validity has an option to parse MikroTik RouterOS config files. You just need `ROUTEROS` method in serializer settings to do it. Why MikroTik instead of other vendors? There are 2 reasons:

* MikroTik configuration is really difficult to parse with TTP.
* At the same time, MikroTik configuration has the same structure as JSON may have. So, it's very easy to translate it using simple Python tools.

!!! warning
    Parser works only with **configuration** which structure strictly follows the `/export` command format.
    If you want to work with operational state (`print`-commands), the easiest way would be to leverage MikroTik REST API and [JSON/YAML](#yaml) serializer.

**Input data:**
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

**Result (as YAML):**
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

### XML
This method translates input XML-formatted text into Python dict using [xmltodict](https://github.com/martinblech/xmltodict) library. It is mainly used together with [Netconf commands](./commands.md#typenetconf).

**Input data:**
```xml
<a>
  <b>one</b>
  <b>two</b>
</a>
```

**Result:**
```json
{"a": {"b": ["one", "two"]}}
```
#### mkarr and mknum

XML extraction method has a few drawbacks:

* all the integers and floats in the original XML will be turned into strings inside JSON
* List of values with one single member will be translated into a plain value with no list at all.

Consider the example above with `<a>` and `<b>`. Let's remove the second `<b>`:<br/>
For `<a><b>one</b></a>` XML the result will be `{"a": {"b": "one"}}` instead of<br/>`{"a": {"b": ["one"]}}`.

These issues can be handled with **JQ Expression** field. Validity introduces two custom JQ functions:

* **mkarr(path)** wraps expression at *path* into a list if it's not already a list.
* **mknum** or **mknum(path)** tries to convert all number-like strings *at path or lower* to numbers. Unlike **mkarr()**, this functions works recursively. <br/>So, `. | mknum` which is equivalent to `. | mknum(.)` will be applied to the entire document and will try to convert all number-like strings to numbers.

Let's suppose that you got the following result of XML to JSON converting:
```json
{"a": {"b": "one"}, "c": "10.2"}
```
After applying this JQ expression
```plain
. | mkarr(.a.b) | mknum
```
you'll get
```json
{"a": {"b": ["one"]}, "c": 10.2}
```

### YAML
This method is used to work with already-prepared YAML or JSON data (don't forget that JSON is a subset of YAML). It suits well if you poll your devices via REST API or your vendor has its own tools to get JSON-formatted config (e.g. `| display json` on Junos).


## Fields

#### Name

The name of the Serializer. Must be unique.

#### Extraction Method

This field defines the way of data parsing, possible choices are described [above](#extraction-methods). After you fill out this field, NetBox UI will display other fields which are specific to selected extraction method.

#### Template

Inside this field at the Serializer page you can view your template defined either via DB or via Data Source.

At the add/edit form this field is used to store TTP or TextFSM Template inside the DB.
This option fits well when you have small templates or just need to quickly test some setup.


#### Data Source and Data File

!!! info
    You can use only one option per one serializer instance: you either define your template via DB (**Template** field) or via link (**Data Source** and **Data File** fields). You can't use both approaches at the same time.

This pair of fields allows you to store Serializer template as a file in a Data Source (likely pointing to a Git repository).

This is the best option if you have plenty of complex Serializers and want to get all the benefits from storing them under version control.

#### JQ Expression

This optional field allows to post-process the parsing result by specifying [JQ](https://jqlang.github.io/jq/) expression.

This feature may be convenient when you poll devices via Netconf or REST. The answer may contain a lot of information, and likely not all of it is useful.

#### Drop XML Attributes

This is the field specific to the XML extraction method. It allows to drop all XML attributes (they start with `@` sign after converting to JSON) from the result. It may be useful when dealing with netconf.


## Bind Serializers to Devices

Binding Serializer to Device is required to be able to serialize device configuration found by **device_config_path**.

!!! note
    You don't need to bind Serializer to Devices if you use direct polling. In this case Serializers are bound to [Commands](commands.md).


There are 3 ways to bind a Serializer to Device:

* Set the serializer at **Manufacturer** level. Go to Manufacturer page at set the serializer via custom fields. This action applies this serializer to all the devices with this Manufacturer.

* Set the serializer at **Device Type** level. Go to Device Type page at set the serializer via custom fields. This action applies this serializer to all the devices with this Device Type and overwrites the value from Manufacturer.

* Set the serializer at the individual **Device** level. Go to Device page at set the serializer via custom fields. This action applies this serializer to one specific device and overwrites the values from Device Type and Manufacturer.


When device has bound Serializer and Data Source you can find out how serialized config looks like at the Device page (**Serialized State** tab) or by using API handle<br/>
`/dcim/devices/<id>/serialized_state/?name=config`
