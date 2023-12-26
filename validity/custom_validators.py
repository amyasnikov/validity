from extras.validators import CustomValidator


class DataSourceValidator(CustomValidator):
    """
    This validator prevents creation of more than one Data Source with "default" mark set to True
    """

    def validate(self, instance):
        DataSource = type(instance)
        if DataSource.__name__ != "DataSource":
            return
        if not instance.cf.get("default"):
            return
        default_datasources = DataSource.objects.filter(custom_field_data__default=True)
        if default_datasources.exclude(pk=instance.pk).count() > 0:
            self.fail("Default repository already exists", field="cf_default")
