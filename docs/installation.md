# Installation


Validity is the [NetBox](https://netbox.dev/) plugin. So, before installing validity you have to install NetBox first. Please refer [NetBox docs](https://docs.netbox.dev/en/stable/installation/) for how to do it.

## System Requirements

| **Python** | **NetBox**      |
|------------|-----------------|
| >=3.10     | 3.4 &#124; 3.5  |

## Installation steps
Once you have installed NetBox, you should follow these steps

* Install validity using pip
```console
pip install netbox-validity
```

* Add validity into your [configuration.py file](https://docs.netbox.dev/en/stable/configuration/)
```
# configuration.py

PLUGINS = [
    "validity",
    # some other plugins here
]
```

* Create DB tables
```console
./manage.py migrate validity
```

* Change plugin settings according to your needs via **PLUGINS_CONFIG** variable. Read more: [Plugin Settings](plugin_settings.md)

!!! warning
    The instruction below is for **NetBox 3.4.x only**. Do not execute it for NetBox 3.5.x or above

* To place Validity [custom scripts](https://docs.netbox.dev/en/stable/customization/custom-scripts/) inside **SCRIPTS_ROOT** directory run
```console
./manage.py linkscripts
```
This command will create symbolic links inside **SCRIPTS_ROOT** for each validity script (originally resided in *validity/scripts*).
!!! note
    if you use [netbox-docker](https://github.com/netbox-community/netbox-docker) as a deployment mechanism, check and fix your volume permissions in **docker-compose.yml**. By default, netbox-docker allows read-only access to SCRIPTS_ROOT, so `./manage.py linkscripts` will fail.
