# User-defined Pollers

Validity is able to perform device polling via custom user-defined pollers. This feature may be useful when:

* existing polling methods must be adjusted to work with specific network equipment (e.g. slightly modify `netmiko` to interact with some ancient switch);
* some completely new polling method must be introduced (e.g. gNMI-based).

## Defining custom Poller

To define your own Poller, two steps must be performed:

* Inherit from `CustomPoller` class to implement your custom polling logic
* Fill out `PollerInfo` structure with Poller meta info

### Implementing Poller class

Here is the minimal viable example of a custom poller class. It uses `scrapli` library to connect to devices via SSH.

Place the following code anywhere within your [PYTHONPATH](https://docs.python.org/3.13/using/cmdline.html#envvar-PYTHONPATH)

```python
from scrapli import Scrapli
from validity.pollers import CustomPoller
from validity.models import Command


class ScrapliPoller(CustomPoller):
    # this class/function is supplied with poller parameters
    driver_factory = Scrapli
    # Scrapli class expects "host" param containing ip address of the device
    host_param_name = 'host'
    # This driver method (if defined) is called to open the connection.
    driver_connect_method = 'open'
    # This driver method (if defined) is called to gracefully close the connection.
    driver_disconnect_method = 'close'

    def poll_one_command(self, driver: Scrapli, command: Command) -> str:
        """
        Arguments:
            driver - object returned by calling driver_factory, usually represents connection to a particular device
            command - Django model instance of the Command
        Returns:
            A string containing particular command execution result
        """
        resp = driver.send_command(command.parameters["cli_command"])
        return resp.result
```

!!! note
    Be aware that every poller class instance is usually responsible for interaction with multiple devices. Hence, do not use poller fields for storing device-specific parameters.


### Filling PollerInfo

Poller Info is required to tell Validity about your custom poller.
Here is the example of the plugin settings:

```python
# configuration.py

from validity.settings import PollerInfo
from my_awesome_poller import ScrapliPoller

PLUGIN_SETTINGS = {
    'validity': {
        'custom_pollers' : [
            PollerInfo(klass=ScrapliPoller, name='scrapli', color='pink', command_types=['CLI'])
        ]
    }
}
```

??? info
    The same setting may be defined via dict as well
    ```python
    # configuration.py

    from my_awesome_poller import ScrapliPoller

    PLUGIN_SETTINGS = {
        'validity': {
            'custom_pollers' : [
                {
                    'class': ScrapliPoller,
                    'name':'scrapli',
                    'color':'pink',
                    'command_types'=['CLI'],
                }
            ]
        }
    }
    ```


PollerInfo parameters:

* **klass/class** - class inherited from `CustomPoller`
* **name** - system name of the poller, must contain lowercase letters only
* **verbose_name** - optional verbose name of the poller. Will be used in NetBox GUI
* **color** - badge color used for "Connection Type" field in the GUI
* **command_types** - list of acceptable [Command](../entities/commands.md) types for this kind of Poller. Available choices are `CLI`, `netconf`, `json_api` and `custom`
