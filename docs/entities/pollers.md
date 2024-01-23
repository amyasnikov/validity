# Pollers

Poller describes a way how specific subset of devices can be polled. It stores information about polling method and required credentials like username or password.

## Fields

#### Name
Name of the Poller. Must be unique.

#### Commands
Set of [Commands](commands.md) which are going to be sent to devices.

#### Connection Type
This field defines the polling backend which will be used for this Poller.

#### Public credentials, Private credentials

These two fields must contain any credentials which will be passed to polling backend on its instantiation
All the values of private credentials will be encrypted after submitting.

!!! info
    Let's consider an example to better understand how it works.
    Let's suppose we have a Poller with:
    * connection type: `netmiko`
    * public credentials: `{"device_type": "cisco_ios", "username": "admin"}`
    * private credentials: `{"password": "admin123"}`
    When polling occurs, public and private credentials are merged (device primary IP will also be added there) and passed to **netmiko.ConnectHandler**
    So, it means that in case of public/private credentials for **netmiko** you can define any keyword arguments [ConnectHandler](https://github.com/ktbyers/netmiko#getting-started-1) is ready to accept.


Private credentials are stored encrypted in the DB, decryption occurs only to pass the value to Polling backend.

!!! warning
    DJANGO_SECRET_KEY is used as an encryption key. Consider it in case of data migrations.


## Binding Pollers to Devices

There are 3 ways to bind a Poller to Device:

* Set the Poller at **Manufacturer** level. Go to Manufacturer page at set the Poller via custom fields. This action applies this Poller to all the Devices with this Manufacturer.

* Set the Poller at **Device Type** level. Go to Device Type page at set the Poller via custom fields. This action applies this Poller to all the devices with this Device Type and overwrites the value from Manufacturer.

* Set the Poller at the individual **Device** level. Go to Device page at set the Poller via custom fields. This action applies this Poller to one specific Device only and overwrites the values from Device Type and Manufacturer.
