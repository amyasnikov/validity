from validity import config


if config.netbox_version >= "4.3.0":
    from .schema import schema
