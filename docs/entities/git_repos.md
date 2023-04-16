# Git Repositories

As you may guess, this entity represents a link to some remote Git repository.
Git Repositories serve 2 purposes inside Validity:

* They provide access to plain device configurations

* They can be referenced by another entity containing any text information. By this moment, those entities are **Tests**, **Name Sets** and **Serializers**.

## Fields

#### Name
Name of the repository must be unique. This name is also used as a local git folder name to store repository data.

#### Git URL

This is the URL for git operations. Place here the same URL you place in `git clone` command.

!!! note
    Currently only **HTTP/HTTPS** based URLs are supported

#### Web URL

This URL is used to display hyperlinks to original files in the repo. This is only the base part of the URL, it should not contain the path inside the repository.
You can use `{{ branch }}` substitution instead of hardcoding branch name inside the URL.
For instance, if you had Github repository `https://github.com/amyasnikov/device_repo`, then your Web URL would be <br/>
`https://github.com/amyasnikov/device_repo/blob/{{branch}}/`


#### Device Config Path

This is the template of the path to device config file inside the repository. You can use [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/templates/) expressions for this template. The only available context variable is `device`.

Let's suppose that you have a repository with device configurations

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


#### Default

This boolean field can define the default repository for all the devices.

Validity allows you to define only one repository as default.

#### Username and Password

These are optional fields for the repositories requiring authentication.

The password is stored encrypted in the DB. `DJANGO_SECRET_KEY` environment variable is used as an encryption key for it.

#### Branch

This is the remote Git branch name. Also, this value is used in the `{{branch}}` substitution for Device Config Path.

#### Head Hash

This is the short version of the commit hash for HEAD git pointer. You can get the same result issuing `git rev-parse --short HEAD` command.

After creating the repository you have to run `Git Repositories Sync` script to get the value in this field.

## Bind repositories to devices
Currently there are 2 ways to bind a repository to device:

* Mark repository as **default**, then all the devices (except the devices from the next point) will be bound to this repository. This is the simplest option. If you have 1 repository that contains all the devices, this is the best option for you.

* Bind repository to a Tenant instance via **custom fields** (you can do it at the Tenant instance edit page) and then bind the device to a Tenant.

## Integration with Scripts

Git Repositories Sync script is maid to pull local copy of the repository from remote.
You can execute it via `Other > Scripts` menu or by pushing `Sync` button at the Repository page.

