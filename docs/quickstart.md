# Quick start

# Video Quick Start

You can figure out how to work with Validity using NetBox Web UI in this video:

[![Watch the video](https://img.youtube.com/vi/Hs2IUE6rKC4/0.jpg)](https://youtu.be/Hs2IUE6rKC4)

# CLI Quick Start
!!! note
    This guide uses [pynetbox](https://github.com/netbox-community/pynetbox) library and regular REST API to interact with NetBox. Going this way facilitates the readability and reproducibility of the guide. Moreover, it may be just more convenient way for an engineer to gather information from code examples rather than from GUI screenshots.
    Of course, **you can do exactly all the same things using web GUI**.


## Polling
Current guide is based on a Git repository as a source of device configuration data. If you want to get device configuration or other data directly from network devices, consider [Quick Start With Polling](quickstart_polling.md) article.


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

### NetBox devices
Create **device1** and **device2** together with some other mandatory models. All of this are just regular NetBox entities, there is nothing related to Validity yet.

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
    role=role.id
)
device2 = nb.dcim.devices.create(
    name='device2',
    site=site.id,
    device_type=devtype.id,
    role=role.id
)
```

### Data Source and Serializer instances
* Create Data Source entity, mark it as default

!!! warning
    Unfortunately, according to this [NetBox bug](https://github.com/netbox-community/netbox/issues/14879), configuration of custom fields for a Data Source is not available through REST API prior to NetBox v3.7.2
    Hence, you may have to set up custom field values via GUI.

```python
data_source = nb.core.data_sources.create(
    name='device_repo',
    type='git',
    source_url='https://github.com/amyasnikov/device_repo',
    parameters={'branch': 'master'},
    custom_fields={
        'default': True,
        'device_config_path': '{{device.name}}.txt',
        'web_url': 'https://github.com/amyasnikov/device_repo/blob/{{branch}}'
    }
)
```

* Create Serializer to translate device configuration into JSON and then bind this Serializer to created devices (e.g. via device type).

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
    template=template
)
devtype.custom_fields = {'serializer': serializer.id}
devtype.save()
```

Now let's run git config sync to download our configs from github.
Unfortunately, it cannot be done via pynetbox. Let's use `requests` to do it.

```python
import requests, time

requests.post(
    f'http://127.0.0.1:8000/api/core/data-sources/{data_source.id}/sync/',
    headers={'Authorization': f'Token {token}'}
)

while (status := nb.core.data_sources.get(id=data_source.id).status.value) != 'completed':
    print(f'Not finished yet, current status: {status}')
    time.sleep(1) # we need to wait until sync finishes
```

Now when plain configs are downloaded from github, we can see how serialized configs look like:

```python
import json

serialized_state = requests.get(
    f'http://127.0.0.1:8000/api/dcim/devices/{device1.id}/serialized_state/',
    params={'name': 'config', 'fields': 'value'},
    headers={'Authorization': f'Token {token}'}
).json()

print(json.dumps(serialized_state['results'][0]['value'], indent=4))
# {
#     "interfaces": [
#         {
#             "address": "10.0.0.1",
#             "mask": "255.255.255.255",
#             "description": "device1 LoopBack",
#             "interface": "Loopback0"
#         },
#         {
#             "address": "10.100.0.254",
#             "mask": "255.255.255.0",
#             "description": "CPE_Access_Vlan",
#             "interface": "Vlan100"
#         }
#     ]
# }
```


### Compliance Test

* Create a Selector. Selector is used to gather some subset of devices to later apply Compliance Tests only to that subset. For now, we just need a selector that gathers all the devices

```python
selector = nb.plugins.validity.selectors.create(name='all', name_filter='.*')
```

* Create Compliance Test that checks that all device interfaces have a description. Bind this test to the selector created previously

```python
expression = '''
jq.all('.interfaces[] | select(.description).interface', device.config) == \
jq.all('.interfaces[].interface', device.config)
'''

test = nb.plugins.validity.tests.create(
    name='iface_description',
    description='all interfaces must have a description',
    expression=expression,
    severity='MIDDLE',
    selectors=[selector.id]
)
```
This test checks the equality of 2 JQ expressions:

1. List of interfaces (interface names) which have `description` parameter
2. List of all interfaces

So, if these 2 lists are equal, then each interface on the device has a description and the test will be marked as passed. Otherwise, the lists will not be equal, and the test will fail.


## Running the script and evaluating the results

Now all the required entities are created, and you can execute the test you've created.
This can be done via **RunTests** script.

```python
resp = requests.post(
    'http://127.0.0.1:8000/api/extras/scripts/validity_scripts/RunTests/',
    headers={'Authorization': f'Token {token}'},
    json={'commit': True, 'data': {'make_report': False}},
)

result_id = resp.json()['result']['id']

while (status := nb.core.jobs.get(id=result_id).status.value) != 'completed':
    print(f'Not finished yet, current status: {status}')
    time.sleep(1) # we need to wait until script finishes
```

Now when the script has finished its work we can check the test results.
You can see that our test is passed for device1 and failed for device2. As you may remember from the beginning, interface **ge0/0/1** from **device2** has no description.

!!! note
    Explanation field contains a list of 2-tuples. First part of the tuple is the part of original expression and the second part is its value.
```python
print(
    json.dumps(
        [result.serialize() for result in nb.plugins.validity.test_results.all()],
        indent=4
    )
)
# [
#     {
#         "id": 1,
#         "url": "http://127.0.0.1:8000/api/plugins/validity/test-results/1/",
#         "display": "iface_description::device1::passed",
#         "test": 1,
#         "device": 1,
#         "dynamic_pair": null,
#         "report": null,
#         "passed": true,
#         "explanation": [
#             [
#                 "jq.all('.interfaces[] | select(.description).interface', device.config)",
#                 [
#                     "Loopback0",
#                     "Vlan100"
#                 ]
#             ],
#             [
#                 "jq.all('.interfaces[].interface', device.config)",
#                 [
#                     "Loopback0",
#                     "Vlan100"
#                 ]
#             ],
#             [
#                 "jq.all('.interfaces[] | select(.description).interface', device.config) == jq.all('.interfaces[].interface', device.config)",
#                 true
#             ]
#         ],
#         "custom_fields": {},
#         "created": "2023-04-07T22:34:05.204671Z",
#         "last_updated": "2023-04-07T22:34:05.204688Z"
#     },
#     {
#         "id": 2,
#         "url": "http://127.0.0.1:8000/api/plugins/validity/test-results/2/",
#         "display": "iface_description::device2::failed",
#         "test": 1,
#         "device": 2,
#         "dynamic_pair": null,
#         "report": null,
#         "passed": false,
#         "explanation": [
#             [
#                 "jq.all('.interfaces[] | select(.description).interface', device.config)",
#                 [
#                     "Loopback0"
#                 ]
#             ],
#             [
#                 "jq.all('.interfaces[].interface', device.config)",
#                 [
#                     "Loopback0",
#                     "ge0/0/1"
#                 ]
#             ],
#             [
#                 "jq.all('.interfaces[] | select(.description).interface', device.config) == jq.all('.interfaces[].interface', device.config)",
#                 false
#             ],
#             [
#                 "Deepdiff for previous comparison",
#                 {
#                     "iterable_item_added": {
#                         "root[1]": "ge0/0/1"
#                     }
#                 }
#             ]
#         ],
#         "custom_fields": {},
#         "created": "2023-04-07T22:34:05.206210Z",
#         "last_updated": "2023-04-07T22:34:05.206231Z"
#     }
# ]
```
