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

```python
from validity.pollers import CustomPoller
from validity.models import Command


class ScrapliPoller(CustomPoller):
    driver_factory = Scrapli
    host_param_name = 'host'  #  Scrapli expects "host" param containing ip address of the device
    driver_connect_method = 'open'  # This driver method (if defined) will be called to open the connection.
    driver_disconnect_method = 'close' # This driver method (if defined) will be called to gracefully close the connection.

    def poll_one_command(self, driver, command) -> str:
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

PollerInfo parameters:

* **klass** - class inherited from `CustomPoller`
* **name** - system name of the poller, must contain lowercase letters only
* **verbose_name** - optional verbose name of the poller. Will be used in NetBox GUI
* **color** - badge color used for "Connection Type" field in the GUI
* **command_types** - list of acceptable [Command](../entities/commands.md) types for this kind of Poller. Available choices are `CLI`, `netconf`, `json_api` and `custom`
