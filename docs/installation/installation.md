# Installation


Validity is the [NetBox](https://netboxlabs.com/oss/netbox/) plugin. So, before installing Validity you have to install NetBox first. Please refer [NetBox docs](https://netboxlabs.com/docs/netbox/en/stable/installation/) for how to do it.

## System Requirements (latest version)

| **Python** | **NetBox**      |
|------------|-----------------|
| >=3.12     | 4.3 &#124; 4.4 &#124; 4.5 |

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

* Add Data Source [custom validator](https://docs.netbox.dev/en/stable/customization/custom-validation/) to prevent creation of more than one Data Source with `default=True`
```
#configuration.py

CUSTOM_VALIDATORS = {
    "core.datasource": ["validity.custom_validators.DataSourceValidator"]
}

```

* Create DB tables
```console
./manage.py migrate validity
```

* Collect static files
```console
./manage.py collectstatic
```

* Change plugin settings according to your needs via **PLUGINS_CONFIG** variable. Read more: [Plugin Settings](plugin_settings.md)
