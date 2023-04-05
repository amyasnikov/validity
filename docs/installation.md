# Installation


Validity is the [NetBox](https://netbox.dev/) plugin. So, before installing validity you have to install NetBox first. Please refer [NetBox docs](https://docs.netbox.dev/en/stable/installation/) for how to do it.

## System Requirements

| **Python** | **NetBox** |
|------------|------------|
| >=3.10     | >=3.4      |

## Installation steps
Once you have installed NetBox, you should follow these steps

* Install validity using pip
```console
pip install validity
```

* Add validity into your [configuration.py file](https://docs.netbox.dev/en/stable/configuration/)
```
# configuration.py

PLUGINS = [
    "validity",
    # some other plugings here
]
```

* Validity requires its own tables inside NetBox database. To create these tables run
```console
./manage.py migrate validity
```


* Validity is shipped with some [custom scripts](https://docs.netbox.dev/en/stable/customization/custom-scripts/) aboard.
These scripts must be placed inside **SCRIPTS_ROOT** directory (`/opt/netbox/netbox/scripts` by default). To do it execute
```console
./manage.py linkscripts
```
This command will create symbolic links inside **SCRIPTS_ROOT** for each validity script (originally recided in *validity/scripts*).
!!! note
    if you use [netbox-docker](https://github.com/netbox-community/netbox-docker) as a deployment mechanism, check and fix your volume permissions in **docker-compose.yml**. By default netbox-docker allows read-only access to SCRIPTS_ROOT, so `./manage.py linkscripts` will fail.
