from extras.plugins import PluginConfig


class NetBoxValidityConfig(PluginConfig):
    name = 'validity'
    verbose_name = 'Validity: Configuration Compliance for Network Devices'
    description = 'This plugin provides simple framework to build your own configuration compliance rule set'
    version = '0.1'
    base_url = 'validity'
    django_apps = ["bootstrap5"]


config = NetBoxValidityConfig
