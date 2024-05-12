from validity import config


if config.netbox_version < "4.0.0":
    from .graphene import schema
# else:
#     from .strawberry.schema import schema
