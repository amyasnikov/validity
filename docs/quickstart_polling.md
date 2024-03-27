# Quick Start: Polling

Validity is able to poll your network devices directly and save the results inside a Data Source (typically you should use already present Data Source called **Validity Polling**).
This guide shows how to work with polling and operational state data.

## Preparing network lab
To follow this guide you need 2 devices running Junos OS. Any Junos 14.2+ (which has **display json**) will suit well.

## Creating entities in NetBox
#### Devices
Create **junos1** and **junos2** instances together with other required NetBox stuff.

```python
from pynetbox.core.api import Api


token = 'get api token via web gui and place it here'

nb = Api(url='http://127.0.0.1:8000', token=token)

# site and role are supposed to be created in previous quick start article
site = nb.dcim.sites.get(slug='site1')
role = nb.dcim.device_roles.get(slug='role1')
juniper = nb.dcim.manufacturers.create(name='Juniper', slug='juniper')
vmx_type = nb.dcim.device_types.create(model='VMX', slug='vmx', manufacturer=juniper.id)

junos1 = nb.dcim.devices.create(
    name='junos1',
    site=site.id,
    device_type=vmx_type.id,
    role=role.id
)
junos2 = nb.dcim.devices.create(
    name='junos2',
    site=site.id,
    device_type=vmx_type.id,
    role=role.id
)
```

#### IP Addresses
To poll devices they have to have **primary IP address**.

Let's create IP Addresss and Interface for each of the devices and bind them together.
```python
# Interface creation
junos1_fxp = nb.dcim.interfaces.create(name='fxp0', device=junos1.id, type='1000base-t')
junos2_fxp = nb.dcim.interfaces.create(name='fxp0', device=junos2.id, type='1000base-t')


# IP Address creation
ip1 = nb.ipam.ip_addresses.create(
    address='192.168.10.1/32',
    status='active',
    assigned_object_type='dcim.interface',
    assigned_object_id=junos1_fxp.id
)
ip2 = nb.ipam.ip_addresses.create(
    address='192.168.10.2/32',
    status='active',
    assigned_object_type='dcim.interface',
    assigned_object_id=junos2_fxp.id
)
```
When IPs are bound to interfaces and interfaces are bound to devices, primary IPs can be assigned to devices

```python
junos1.primary_ip4 = ip1.id
junos2.primary_ip4 = ip2.id

junos1.save()
junos2.save()
```
Now both devices have Primary IP and are ready to be polled.

#### Commands and Poller
Let's set up 2 [Commands](entities/commands.md):

* **show configuration**
* **show chassis routing-engine**

```python
# json serializer
json_serializer = nb.plugins.validity.serializers.create(name='JSON/YAML', extraction_method='YAML')

show_config = nb.plugins.validity.commands.create(
    name='Show configuration',
    label='show_config',
    retrieves_config=True,
    serializer=json_serializer.id,
    type='CLI',
    parameters={'cli_command': 'show configuration | display json | no-more'}
)
show_re = nb.plugins.validity.commands.create(
    name='Show chassis RE',
    label='show_re',
    serializer=json_serializer.id,
    type='CLI',
    parameters={'cli_command': 'show chassis routing-engine | display json | no-more'}
)
```

After that let's create a Poller which describes how to connect to our Junos devices.

```python
junos_poller = nb.plugins.validity.pollers.create(
    name='Junos Poller',
    commands=[show_config.id, show_re.id],
    connection_type='netmiko',
    public_credentials={'device_type': 'juniper_junos', 'username': 'admin'},
    private_credentials={'password': 'admin_123'}
)
```

Finally, Poller has to be bound to appropriate Devices. Let's do it at Manufacturer level.

```python
juniper.custom_fields = {'poller': junos_poller.id}
juniper.save()
```

## Performing Polling

For polling purposes Validity creates one special Data Source: **Validity Polling**. "Sync" of this Data Source causes polling of all bound Devices.

Binding of devices to Data Source can be done in 2 ways: either by marking the Data Source as default or by assigning the Data Source to a Tenant which contains required devices.

Let's create a Tenant with bound Data Source and bind our Junos devices to this Tenant.
```python
validity_polling = nb.core.data_sources.get(name='Validity Polling')

tenant1 = nb.tenancy.tenants.create(
    name='tenant1',
    slug='tenant1',
    custom_fields={'data_source': validity_polling.id}
)

junos1.tenant = tenant1.id
junos2.tenant = tenant1.id

junos1.save()
junos2.save()
```

Now the Devices have both Data Source and Poller bound, and it's sufficient to poll them.

```python
import requests, time

requests.post(
    f'http://127.0.0.1:8000/api/core/data-sources/{validity_polling.id}/sync/',
    headers={'Authorization': f'Token {token}'}
)

while (status := nb.core.data_sources.get(id=validity_polling.id).status.value) != 'completed':
    print(f'Not finished yet, current status: {status}')
    time.sleep(1) # we need to wait until sync finishes
```

When polling is finished we can check out serialized state for our Devices.

```python
print(
    requests.get(
        f'http://127.0.0.1:8000/api/dcim/devices/{junos1.id}/serialized_state/',
        headers={'Authorization': f'Token {token}'}
    ).json()
)
```

Finally, this serialized state can be used in [Compliance Tests](entities/tests.md) via `device.config` and `device.state.show_re` statements. Visit [Quick Start](quickstart.md#compliance-test) article to find more info about creating and executing Compliance Tests.
