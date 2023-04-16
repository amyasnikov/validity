# How to write Test Expressions

This article contains some of the possible approaches for writing effective Test Expressions.


### Use JQ to extract data from your config

[JQ](https://stedolan.github.io/jq/) is super powerful in extracting/transforming various JSON data. In many cases write a JQ expression is shorter and easier than write a Python one.

!!! note
    `jq()` function always returns a list due to an original CLI tool which may return multiple answers.
    For instance, `jq('2 + 2', {})` returns `[4]`.
    To return a single answer you can use `jq.first(expression, object)`

Let's write a test that finds all the unused routing policies on a device. "Unused" means the policy is created on a device but is not applied anywhere.
The main problem here is the routing policy versatility. It can be applied to:

* BGP neighbor in/out
* BGP group in/out
* incoming/outgoing updates in distance vector protocols (EIGRP, RIP)
* redistribution from any protocol to any other protocol
* all the above inside the different VRFs
* many other purposes that depend on a particular vendor

So, what we need to do is just to recursively traverse all the config and find all the occurrences of a particular policy name.
This JQ expression finds all the occurrences of the *some_policy_name* as some dictionary or list value and outputs the number of times it was used:

```
[.. | select(type == "string" and . == "some_policy_name")] | length
```

[Check online](https://jqplay.org/s/UY7EF0BCUur)

Our next subtask is to extract all routing policy names. It depends heavily on your serialized config schema. Let's imagine something like this:
```yaml
routing-policies:
- name: policy1
  terms: [...]
- name: policy2
  terms: [...]
```
So, we'll extract policy names list with 

```
."routing-policies"[].name
```

[Check online](https://jqplay.org/s/-56gmv4nAjf)

The next step is to tie together 2 previous expressions. Get all policy names and feed them into usage counter.

```
."routing-policies"[].name as $pol_name
| [.. | select(type == "string" and . == $pol_name)] | length
```

[Check online](https://jqplay.org/s/BTlUDRyOW-T)

Let's also remove `."routing-policies"` subtree from the usage calculations

```
."routing-policies"[].name as $pol_name
| [
    del(."routing-policies") | .. | select(type == "string" and . == $pol_name)
] | length
```

[Check online](https://jqplay.org/s/R8sp_op8cik)

Now we've got real usage numbers for each of the policies. We could stop here and check for zeros in the resulting array, e.g. using python `all()` function. This would be a valid test expression.

The problem arises when some user sees the fail of this test and wants to fix device config. The test does not output policy names with zero usage and the user (network engineer) has to spend some time to find them by himself.

Let't create an array where policy name is the key and usage counter is the value:

```
[
    ."routing-policies"[].name as $pol_name
    | {
        key: $pol_name,
        value: (
            [
                del(."routing-policies") 
                | .. 
                | select(type == "string" and . == $pol_name)
            ] | length
        )
    }
] | from_entries
```

[Check online](https://jqplay.org/s/JidrghIjEAE)


Here we feed policy names found in `."routing-policies"` into a dictionary creation expression. Key of the dictionary is the policy name, and the value is usage counter we wrote before.

The last thing to do is to check that there would be no zeros in the dictionary values

```python
all(
    jq.first('''
        [
            ."routing-policies"[].name as $pol_name
            | {
                key: $pol_name,
                value: (
                    [
                        del(."routing-policies") 
                        | .. 
                        | select(type == "string" and . == $pol_name)
                    ] | length
                )
            }
        ] | from_entries
        ''',
        device.config
    ).values()
)
```

Someone may ask what have changed since the previous expression with the usage counters only. We still check the usage counters and ignore policy names. The difference is the **explanation** value of the Test Result. Explanation for the last one expression will show policy names and the respective usage count.


### Use dynamic pairs to compare paired device configs

Let's suppose that we have 2 switches with EVPN Active-Active feature configured. This feature particularly requires the interfaces that physically point to the same L2 segment to have the same ESI identifier configured. Let's suppose also that by our network design interfaces with the same number always point to the same segment.

So, in our test we'll check that the same interfaces on pair switches have the same ESI identifiers.
Let's suppose that a device has the following serialized config:

```yaml
interfaces:
- name: ge-0/0/1
  esi: '0000.0000.0000.0000.1001'
- name: ge-0/0/2
  esi: '0000.0000.0000.0000.1002'
- name: ge-0/0/3
  esi: '0000.0000.0000.0000.1003'
```

This JQ expression forms a dictionary with interface name as a key and ESI as a value. Interfaces without an ESI are thrown away.
```
[.interfaces[] | select(.esi != null)] | map({"key": .name, "value": .esi}) | from_entries
```

[Check online](https://jqplay.org/s/KHaZOCnAeTa)

Now all we have to do is to compare these dictionaries for a device and for its dynamic pair

```python
jq.first(
    '[.interfaces[] | select(.esi != null)] | map({"key": .name, "value": .esi}) | from_entries',
    device.config
) == jq.first(
    '[.interfaces[] | select(.esi != null)] | map({"key": .name, "value": .esi}) | from_entries',
    device.dynamic_pair.config 
)
```

!!! info
    Double usage of the same JQ expression above looks like a good opportunity to move it out into a nameset function.


### Use Config Contexts to compare desired state with operational state

NetBox has a built-in feature called [Configuration Contexts](https://demo.netbox.dev/static/docs/features/context-data/). This feature could be leveraged for writing some kind of a device desired state. When we have desired state, we can compare it with the operational state (the real config from the device).

Let's suppose that you are dealing with multicast routing via PIM SM. One of the requirements of the proper work of this protocol is to have the same Rendezvous-Point (RP) IP address on all the routers. So, we want to check it using Validity.

The first thing that might come in mind is to collect RP addresses from all the routers and compare between each other. Unluckily, Validity has no built-in options to compare more than 1 device between each other. You still might use ORM and some tricky queries, but this is the difficult way.

The more straightforward approach is to define target RP address in configuration context and then compare it with the value in device config. Due to hierarchical behavior of config contexts you can define RP address one time, e.g. for the whole `Site` entity, the value will be inherited by the individual devices of this site.

The test in this case will be very simple:

```python
device.config['protocols']['pim']['rp_address'] == device.get_config_context()['rp_address']
```

### Use DCIM info to compare connected neighbors

!!! note
    This is a relatively difficult approach comparing to the others. **If it is possible**, you should prefer using config contexts or dynamic pairs due to the greater simplicity of the test expressions with these approaches.

Sometimes you may need to write a test that leverages the information about various physical connections between the devices. One common example is to check that VLANs on your trunk port match the VLANs on the neighbor which is connected in this port.

Consider this serialized config:

```yaml
interfaces:
- name: ge0/0/1
  trunk_vlan:
  - 10
  - 12
  - 100
- name: ge0/0/2
  trunk_vlan:
  - 20
  - 30
```

Let's use config contexts from previous topic to define trunk ports which we want to check. This expression lists all the neighboring devices which are connected to target trunk ports

```python
[
    iface.connected_endpoints[0].device
    for iface in device.interfaces.filter(
        name__in=device.get_config_context()['trunk_ports']
    )
]
```


Now we extend this expression to compare the *trunk_vlan* contents from the device and from its neighbor for each of the trunk ports.

```python
[
    jq.first(
        f'.interfaces[] | select(.name=="{iface.connected_endpoints[0].name}")',
        iface.connected_endpoints[0].device.config
    ) == jq.first(f'.interfaces[] | select(.name=="{iface.name}")', device.config)
    for iface in device.interfaces.filter(
        name__in=device.get_config_context()['trunk_ports']
    )
]
```

So, we've got a list of True or False where True means the equality of the trunk_vlan list and False means the opposite.
The final step is to check that all the values in the list are True. Python has a built-in function `all()` to do this.

```python
all([
    jq.first(
        f'.interfaces[] | select(.name=="{iface.connected_endpoints[0].name}")',
        iface.connected_endpoints[0].device.config
    ) == jq.first(f'.interfaces[] | select(.name=="{iface.name}")', device.config)
    for iface in device.interfaces.filter(
        name__in=device.get_config_context()['trunk_ports']
    )
])
```
