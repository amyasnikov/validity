# Commands

Commands are executed on the devices and then respective command output is saved. This output can later be serialized and used in compliance tests.
One Command can belong to one or more [Pollers](pollers.md) (binding is performed through Poller form).


## Fields

#### Name
The Name of the Command. Must be unique.

#### Label
Slug-like label of the Command. Value must follow the rules:
* contain only ASCII letters, numbers and underscores
* start with a letter

Label value is used to access serialized command output in Compliance Test.
E.g. test expression `device.state.sh_version` implies there is a Command with label `sh_version`.

#### Type
Type of the command. It defines other parameters that must be filled for this command. Right now only **CLI** type is available, but more types will appear in next releases.

#### Retrieves configuration
Defines either this command is supposed to retrieve device configuration or no. For each poller there can be **at most one** command which retrieves configuration.

!!! note
    Serialized state for command which retrieves configuration is always available through "config" key. Let's suppose we have a command with label `show_run` which has `retrieves_config=True`, then inside Compliance Test the serialized output of this command will be available through both `device.state.show_run` and `device.state.config`.

#### Serializer
This field defines [Serializer](serializers.md) for Command output.

## Parameters
This block contains type-specific parameters.

### Type:CLI
#### CLI Command
This field contains text string which is going to be sent to device when polling occurs. 