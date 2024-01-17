from functools import partial

import pytest
from core.models import DataSource
from django.core.exceptions import ValidationError

from validity.custom_validators import DataSourceValidator


@pytest.mark.django_db
def test_device_validator(create_custom_fields):
    validator = DataSourceValidator()
    GitDataSource = partial(DataSource, source_url="http://ab.io/d", type="git")
    data_source1 = GitDataSource(name="ds1", custom_field_data={"default": True})
    validator.validate(data_source1)
    data_source1.save()
    data_source2 = GitDataSource(name="ds2", custom_field_data={"default": True})
    with pytest.raises(ValidationError):
        validator.validate(data_source2)
    data_source3 = GitDataSource(name="ds3", custom_field_data={"default": False})
    validator.validate(data_source3)
