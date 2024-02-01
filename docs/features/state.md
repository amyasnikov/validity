# Device State and How It Is Filled

**State** is a special dict-like object which contains serialized configuration or/and serialized command outputs for a particular Device instance. State contents can be accessed inside [Compliance Test](../entities/tests.md) code via `device.state.<command_label>` expression. If command has `retrieves_config=True` option, its serialized contents are available through `device.state.config`.

!!! note
    `device.config` is the backward compatible shortcut for `device.state.config`

`device.state.config` may be filled via 2 different options:

* if Device has bound [Poller](../entities/pollers.md) and this Poller has bound [Command](../entities/commands.md) which has `retrieves_config=True`, then serialized output of this Command will be inserted into `device.state.config`
* if Device has bound [Serializer](../entities/serializers.md) and [Data Source](../entities/datasources.md) which has `device_config_path` set, then serialized contents of the file defined by `device_config_path` will be written inside `device.state.config`.

When both options are applicable, the last one takes precedence over the first one.

The user can always check out the contents of **State** either on **Serialized State** Device GUI tab or via `/api/dcim/devices/{device_id}/serialized_state/` REST API endpoint.

This endpoint has 2 optional query params:

* **name** - allows filtering State items by their names. Example: `?name=config&name=show_version`
* **fields** - allows displaying specified fields only. Example: `?fields=name&fields=value`
