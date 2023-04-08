# Git Repositories

As you may guess, this entity represents a link to some remote Git repository.
Git Repositories serve 2 purposes inside Validity:
* They provide an access to plain device configurations
* They can be referenced by another enitity containing any text informarion. By this moment, those entities are Tests, Name Sets and Serializers.

## Fields

### Name
Name of the repository must be unique. This name is also used as a local git folder name to store repository data.

### Git URL

This is the URL for git operations. Place here the same URL you place in `git clone` command.

!!! note
    Currently only HTTP/HTTPS based URLs are supported

### Web URL

This URL is used to display hyperlinks to original files in the repo. This is only the base part of the URL, it should not contain the path inside the repository.
You can use `{{ branch }}` substitution instead of hardcoding branch name inside the URL.
For instance, if you had Github repository `https://github.com/amyasnikov/device_repo`, then your Web URL would be <br/>
`https://github.com/amyasnikov/device_repo/blob/{{branch}}/`


### Device Config Path

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

`{{ device.location.slug | lower }}/{{ device.name }}.cfg`

### Username and Password

These are optional fields for the repositories requiring authentication.

The password is stored encrypted in the DB. `DJANGO_SECRET_KEY` environment variable is used as an encryption key for it.

### Branch

This is the remote Git branch name. Also, this value is used in the `{{branch}}` substitution for Device Config Path.

### Head Hash

This is the short version of the commit hash for HEAD git pointer. You can get the same result issuing `git rev-parse --short HEAD` command.

After creating the repository you have to run `Git Repositories Sync` script to get the value in this field.
