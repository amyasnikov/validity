# Pollers

Poller describes a way how specific subset of devices can be polled. It stores information about polling method and required credentials like username or password.

## Fields

#### Name
Name of the Poller. Must be unique.

#### Commands
Set of [Commands](commands.md) which are going to be sent to devices.

#### Connection Type
This field defines the library used to interact with devices (polling backend). At the moment there are 3 options available:

* [netmiko](https://github.com/ktbyers/netmiko) for polling via SSH or Telnet
* [scrapli_netconf](https://github.com/scrapli/scrapli_netconf) for polling via Netconf
* [requests](https://github.com/psf/requests) for polling via REST or JSON API

#### Public credentials, Private credentials

These two fields must contain any credentials which will be passed to polling backend.
All the values of private credentials will be encrypted after submitting. These values are stored encrypted in the DB, decryption occurs only to pass the value to Polling backend.

!!! warning
    DJANGO_SECRET_KEY is used as an encryption key. Consider it in case of data migrations.


## Credentials and polling backend

Let's consider an example to better understand how credentials are passed to selected Conenction Type.
Let's suppose we have a Poller with:

* connection type: `netmiko`
* public credentials: `{"device_type": "cisco_ios", "username": "admin"}`
* private credentials: `{"password": "admin123"}`

When polling occurs, public and private credentials are merged (device primary IP will also be added there) and passed to **netmiko.ConnectHandler**
So, it means that in case of public/private credentials for **netmiko** you can define any keyword arguments [ConnectHandler](https://github.com/ktbyers/netmiko#getting-started-1) is ready to accept.


The table below points out the entities which accept merged credentials from poller:

| Connection Type | Entity that accepts credentials      |
|-----------------|--------------------------------------|
| netmiko         | netmiko.ConnectHandler               |
| scrapli_netconf | scrapli_netconf.driver.NetconfDriver |
| requests        | requests.request                     |

For **requests** case there is some extra logic here:

1. `url` credential accepts Jinja2 expression, `device` and `command` are available as context variables. Default URL value:<br/>
`https://{{device.primary_ip.address.ip}}/{{command.parameters.url_path.lstrip('/')}}`
2. Pass something like `{"auth": ["admin_user", "admin_password"]}` to use basic auth.
3. SSL verification is turned off by default. You can turn it back on by specifying `{"verify": true}`


## Binding Pollers to Devices

There are 3 ways to bind a Poller to Device:

* Set the Poller at **Manufacturer** level. Go to Manufacturer page at set the Poller via custom fields. This action applies this Poller to all the Devices with this Manufacturer.

* Set the Poller at **Device Type** level. Go to Device Type page at set the Poller via custom fields. This action applies this Poller to all the devices with this Device Type and overwrites the value from Manufacturer.

* Set the Poller at the individual **Device** level. Go to Device page at set the Poller via custom fields. This action applies this Poller to one specific Device only and overwrites the values from Device Type and Manufacturer.
