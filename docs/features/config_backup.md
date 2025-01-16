# Configuration Backup

Validity supports device configurations backups to remote **Git** or **S3** server(s).

## Backup provisioning

1. Follow the steps described in the [Quickstart: Polling](../quickstart_polling.md) article to set up all the entities required for device polling.

2. Polling is done when the Data Source is synced. In most cases it will be the default **Validity Polling** Data Source, but you are free to create your own one with the type *device_polling*.

3. Create a [Backup Point](../entities/backuppoints.md) which describes a place where the Data Source with the configs have to be uploaded.

Example using pynetbox:

```python
import pynetbox

nb = pynetbox.api('http://localhost:8000', token=nb_token)

validity_polling = nb.core.data_sources.get(name="Validity Polling")

nb.plugins.validity.backup_points.create(
    name='my_github_repo',
    data_source=data_source.id,
    upload_url='https://github.com/amyasnikov/my_repo',
    method='git',
    parameters={"username": "amyasnikov", "password": github_token}
)
```

## Backing Up

There are several options to trigger the backup process:

* Press "Back Up" button on the Backup Point page.

* Specify `Backup After Sync: True` in the Backup Point settings. This will trigger the backup process each time the respective data source is being synced (no matter via button, API or somehow else).

* Execute [RunTests](../entities/scripts.md#run-tests) script with `Sync Data Sources: True` option (`Backup After Sync: True` is required as well).


### Options for periodic backup

There are several options to provision periodic configuration backup process (e.g. daily, each 6 hours, etc):

1. Provision [RunTests](../entities/scripts.md#run-tests) script to execute on a regular basis using **Interval** script parameter. This will run everything at once:
    * poll the devices (perform data source sync)
    * execute compliance tests
    * back up the data source


2. If you don't want to run the tests via scheduler and want backup only, you can create tiny [custom script](https://netboxlabs.com/docs/netbox/en/stable/customization/custom-scripts/) inside your NetBox and configure it to run periodically.

```python
from core.models import DataSource
from extras.scripts import Script, ObjectVar

class SyncDataSource(Script):
    data_source = ObjectVar(model=DataSource)

    def run(self, data, commit):
        data['data_source'].sync()

```

Execution of this script triggers the sync of the DataSource (and hence the backup process for bound Backup points with `Backup After Sync: True`).

3. Wait till periodic Data Source sync is implemented in the core NetBox. There is an [issue](https://github.com/netbox-community/netbox/issues/18287) for it, upvotes are appreciated.
