# 1.4.0

New Features:
* Added support for NetBox 3.6. **Be careful. NetBox 3.6.0 and 3.6.1 have NO support due to [this](https://github.com/netbox-community/netbox/issues/13757) bug**


# 1.3.2

Bug Fixes:
#54 - prevent creation of ScriptModule from .pyc files


# 1.3.1

Bug Fixes:
* #53 Syntax highlighting wasn't available in non-development installation


# 1.3.0

New Features:
* Per Device Compliance Reports. See [screenshot](https://github.com/amyasnikov/validity/blob/master/docs/images/screen_report.png)
* Syntax highlighting for Python code

Bug Fixes:
* #46 Problem with running under Python3.11
* #28 Multiline test result explanations had a lot of "\n" symbols

P.S. Don't forget to issue `./manage.py collectstatic` to turn on syntax highlighting


# 1.2.1

Bug Fixes:
* Fix #44, absence of validity scripts in NetBox 3.5


# 1.2.0

New features:
* GraphQL API introduced
* Dynamic pairs now can be composed by a Tag. See [docs](https://validity.readthedocs.io/en/latest/features/dynamic_pairs/#by-tag)
* Dynamic Pair value now can be viewed at Selector page (**Bound Devices** table)
* NetBox global search enabled for the plugin
* Minor UI improvements

Bug Fixes:
* Tables paginator appearance fix

---
P.S Don't forget to apply migrations via `./manage.py migrate validity`  when upgrading from previous versions


# 1.1.0

New Features:

* NetBox 3.5 support added
* Added Mikrotik RouterOS separate parser (extraction method). See [docs](https://validity.readthedocs.io/en/latest/entities/serializers/#mikrotik-parsing)
* The tests now can be executed for specific subset of devices (may be useful for automation workflows)


# 1.0.1

Bug fixes:
* PYPI installation fixed
* Minor fixes
