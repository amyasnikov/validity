# Upgrading to a new Validity release

Upgrade process is pretty straightforward:

* Make sure your NetBox version [is compatible](./netbox_compatibility.md) with the new Validity version

* Update the package version through pip

```
pip install --upgrade netbox-validity
```

* Run `migrate` and `collectstatic` management commands

```
./manage.py migrate
./manage.py collectstatic
```


## Major release upgrade

Major version upgrade (e.g. v2.x -> v3.x) may require some additional rules:

* Don't skip major version upgrades (e.g. don't upgrade 1.4.1 directly to 3.0.0)
* Before upgrading major version number, install the latest minor version first

For example, you want to upgrade from 2.1.1 to 3.0.0. To do this you have to

* install 2.3.3 (the latest available v2 release) first according to the procedure described above
* install 3.0.0
