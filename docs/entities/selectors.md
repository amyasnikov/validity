# Selectors

Selector is a flexible way to choose some subset of devices and then apply compliance tests only to these devices.

This works in the following manner: you define one or more filters and choose how to join these filters (using `OR` or `AND`) together. Next you can find out which devices were chosen by a selector at the selector web page. Later you can bind some compliance tests to this selector. These compliance tests will be executed against all the devices matched by this selector.


An additional purpose of a selector is to define how dynamic pairs for the devices are formed.

!!! Warning
    Bear in mind that one device could belong to different selectors. If you applied the same test to multiple selectors containing the same device, this test will be executed multiple times for this device.


## Fields

#### Name

The name of the selector. Must be unique.

#### Multi-filter operation

Choice field: `OR` or `AND`
This field defines how multiple filter fields interact between each other.

For example, we have a Selector with **Name filter** equal to `asw` and **Site filter** equal to `London`.

In this case, Multi-filter Operation equal to `OR` will select all the devices that contain `asw` **plus** all the devices from London.

On the other hand, Multi-filter Operation equal to `AND` will select all `asw` devices that belong to `London` site.


#### Device Name Filter

This field can filter devices by their names. You can use regular expressions syntax to make complex filters. **Search** logic is applied to the contents of the filter. It means that `asw[0-9]{2}` filter will match both `asw01-london` and `london-asw01`.

Name filter has an additional purpose: to make a rule for dynamic pairs creation. You can read more about it in the [Dynamic Pairs](../dynamic_pairs.md) reference.


#### Status Filter
This filter allows to filter device by its `status` field.

#### Other filters

* Tag Filter
* Manufacturer Filter
* Device Type Filter
* Platform filter
* Location filter
* Site filter

All of this are some properties of the device that you can filter by. In any of these fields you can use multiple values. Multiple values in single field has `OR` logic (and this is completely independent from Multi-filter operation).
For instance, if you have Location filter "`room-403`, `room-404`", this will select both the devices from room 403 and from 404.

#### Dynamic Pairs
This field manages the creation of dynamic pairs during the test.
For now it has 2 possible values:

* **NO** - dynamic pairs won't be created
* **By name** - dynamic pairs will be created according to the **Device Name Filter** value

More info: [Dynamic Pairs](../dynamic_pairs.md).
