from extras.validators import CustomValidator


class DataSourceValidator(CustomValidator):
    """
    This validator prevents creation of more than one Data Source with "device_config_default" mark set to True
    """

    def validate(self, instance):
        DataSource = type(instance)
        if DataSource.__name__ != "DataSource":
            return
        if not instance.cf.get("device_config_default"):
            return
        default_datasources = DataSource.objects.filter(custom_field_data__device_config_default=True)
        if default_datasources.exclude(pk=instance.pk).count() > 0:
            self.fail("Default repository already exists", field="cf_device_config_default")
