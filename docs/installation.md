# Installation


Validity is the [NetBox](https://netbox.dev/) plugin. So, before installing validity you have to install NetBox first. Please refer [NetBox docs](https://docs.netbox.dev/en/stable/installation/) for how to do it.

## System Requirements

| **Python** | **NetBox**      |
|------------|-----------------|
| >=3.10     | 3.5 &#124; 3.6 &#124; 3.7 |

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
!!! warning
    According to [this NetBox bug](https://github.com/netbox-community/netbox/issues/14349) custom validation for Data Source **does not work** prior to NetBox v3.6.6


* Create DB tables
```console
./manage.py migrate validity
```

* Collect static files
```console
./manage.py collectstatic
```

* Change plugin settings according to your needs via **PLUGINS_CONFIG** variable. Read more: [Plugin Settings](plugin_settings.md)
