# Data Sources

Data Source is a native NetBox entity which is actively used by Validity.
Data Source can be used in the following ways:

* Store configuration or state data for all or particular devices
* Be referenced by another entity containing any text information. By this moment, these entities are **Tests**, **Name Sets** and **Serializers**.
* Data Source called **Validity Polling** (with type **device_polling**) is used to poll network devices and collect gathered information

## Custom Fields

#### Default

This boolean field can define the default repository for all the devices.

Validity allows you to define only one repository as default.


#### Web URL

This URL is used to display hyperlinks to original files in the repo. This is only the base part of the URL, it should not contain the path inside the repository.
You can use `{{ branch }}` substitution instead of hardcoding branch name inside the URL.
For instance, if you had Github repository `https://github.com/amyasnikov/device_repo`, then your Web URL would be <br/>
`https://github.com/amyasnikov/device_repo/blob/{{branch}}/`


#### Device Config Path

This is the template of the path to device config file inside the Data Source. You can use [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/templates/) expressions for this template. The only available context variable is `device`.

Let's suppose that you have a Data Source with device configurations

```console
device_repo
├── london
│   ├── asw01-london.cfg
│   └── asw02-london.cfg
└── paris
    ├── asw01-paris.cfg
    └── asw02-paris.cfg
```
Then you may end up with the following device config path:

`{{ device.site.slug | lower }}/{{ device.name }}.cfg`


#### Device Command Path
This is the template of the path to specific command output for specific device.
In most cases you don't need this variable and may omit it.

It is required for repositories where you're going to extract operational state data related to specific commands (you may notice this field is filled for **Validity Polling** data source).

Jinja2 can be used as well and two available context variables are `device` and `command`,


## Bind Data Sources to Devices
Currently there are 2 ways to bind a repository to device:

* Mark Data Source as **default**, then all the devices (except the devices from the next point) will be bound to this Data Source. This is the simplest available option.

* Bind repository to a Tenant instance via **custom fields** (you can do it at the Tenant instance edit page) and then bind the device to a Tenant.
