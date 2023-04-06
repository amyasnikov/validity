# Quickstart


!!! note
    This guide uses [pynetbox](https://github.com/netbox-community/pynetbox) library to interact with NetBox. Going this way facilitates the readability and reproducibility of the guide. Moreover, it may be just more convenient way for an engineer to gather information from code examples rather than from GUI screenshots.
    Of course, you can do exactly all the same things using web GUI.


## Preparing Git repository

* Create repository on github.com with device configurations. E.g. <br/>
`https://github.com/amyasnikov/device_repo`

* Place 2 config files in the root of the repository

<table>
<tr>
<th>device1.txt</th>
<th>device2.txt</th>
</tr>
<tr>
<td>
<pre><code>
interface Loopback0
 description device1 LoopBack
 ip address 10.0.0.1 255.255.255.255
!
interface Vlan100
 description CPE_Access_Vlan
 ip address 10.100.0.254 255.255.255.0
!
</code></pre>
</td>
<td>
<pre><code>
interface Loopback0
 description device2 LoopBack
 ip address 10.0.0.2 255.255.255.255
!
interface ge0/0/1
 ip address 10.10.10.1 255.255.255.252
!
</code></pre>
</td>
</tr>
</table>


## Creating entities in NetBox

* Create **device1** and **device2** together with some other mandatory models. All of this are just regular NetBox entities, there is nothing related to Validity yet.

```python
from pynetbox.core.api import Api


token = 'get api token via web gui and place it here'

nb = Api(url='http://127.0.0.1:8000', token=token)

site = nb.dcim.sites.create(name='site1', slug='site1')
role = nb.dcim.device_roles.create(name='role1', slug='role1', color='ffffff')
mf = nb.dcim.manufacturers.create(name='manufacturer1', slug='manufacturer1')
devtype = nb.dcim.device_types.create(model='model1', slug='model1', manufacturer=mf.id)

device1 = nb.dcim.devices.create(
    name='device1',
    site=site.id,
    device_type=devtype.id,
    device_role=role.id
)
device2 = nb.dcim.devices.create(
    name='device2',
    site=site.id,
    device_type=devtype.id,
    device_role=role.id
)
```

* Create **device_repo** Repository entity, mark it as default

```python
repo = nb.plugins.validity.git_repositories.create(
    name='device_repo',
    git_url='https://github.com/amyasnikov/device_repo',
    web_url='https://github.com/amyasnikov/device_repo/blob/{{branch}}',
    device_config_path='{{device.name}}.txt',
    branch='master',
    default=True,
)
```

* Create Config Serializer to translate device configuration into JSON and then bind this serializer to created devices (e.g. via device type).

```python
template = '''
<group name="interfaces">
interface {{ interface }}
 ip address {{ address }} {{ mask }}
 description {{ description | ORPHRASE }}
</group>
'''

serializer = nb.plugins.validity.serializers.create(
    name='serializer1',
    extraction_method='TTP',
    ttp_template=template
)
devtype.custom_fields = {'config_serializer': serializer.id}
devtype.save()
```

* Create a selector. Selector is used to gather some subset of devices to later apply compliance tests only to that subset. For now we just need a selector that gathers all the devices

```python
selector = nb.plugins.validity.selectors.create(name='all', name_filter='.*')
```

* Create Compliance Test that checks that all device interfaces have a description. Bind this test to the selector created previously

```
expression = '''
jq('.interfaces[] | select(.description).interface', device.config) == \ 
jq('.interfaces[].interface', device.config)
'''

test = nb.plugins.validity.tests.create(
    name='iface_description',
    description='all interfaces must have a description',
    expression=expression,
    severity= "MIDDLE",
    selectors=[selector.id]
)
```
This test checks the equality of 2 JQ expressions:

1. List of interfaces (interface names) which have `description` parameter
2. List of all interfaces

So, if these 2 lists are equal, then each interface on the device has a description and the test would be marked as passed. Otherwise, the lists would not be equal and the test would fail.


## Running the script and evaluating the results

Now all the required entities are created and you can execute the test you created.
Suddenly, pynetbox has no ability to execute custom scripts. Let's use `requests` to do it.

```python
import time, requests

resp = requests.post(
    'http://127.0.0.1:8000/api/extras/scripts/validity_run_tests.RunTestsScript/',
    headers={'Authorization': f'Token {token}'},
    json={'commit': True, 'data': {'sync_repos': True, 'make_report': False}},
)

result_id = resp.json()['result']['id']

while (status := nb.extras.job_results.get(id=result_id).status.value) != 'completed':
    print(f'Not finished yet, current status: {status}')
    time.sleep(5) # we need to wait until script finishes
```

Now when the script have finished its work we can check the test results.

```python
from pprint import pprint

pprint(
    [result.serialize() for result in nb.plugins.validity.test_results.all()]
)
```
