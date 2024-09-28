from functools import partial as pt

import pytest
from django.db.models import Model
from factories import DataFileFactory, SerializerDBFactory, SerializerDSFactory

from validity import forms, models


class TestSerializerForm:
    @pytest.fixture
    def create_aux_objects(self):
        DataFileFactory()

    def _check_fields(self, instance, fields_to_check):
        for field_name, field_value in fields_to_check.items():
            attrib = getattr(instance, field_name)
            if isinstance(attrib, Model):
                attrib = attrib.pk
                field_value = int(field_value)
            assert attrib == field_value

    @pytest.mark.parametrize(
        "form_data, fields_to_check",
        [
            (fdata := {"name": "s1", "extraction_method": "TTP", "template": "q"}, fdata),
            (fdata := {"name": "s1", "extraction_method": "TTP", "data_source": "1", "data_file": "1"}, fdata),
            (fdata := {"name": "s2", "extraction_method": "ROUTEROS", "template": "q"}, fdata | {"template": ""}),
            (
                {"name": "s", "extraction_method": "YAML", "jq_expression": ".qwe.rty"},
                {"extraction_method": "YAML", "parameters": {"jq_expression": ".qwe.rty"}},
            ),
            (
                {"name": "s", "extraction_method": "XML", "jq_expression": ".qwe", "drop_attributes": "true"},
                {"extraction_method": "XML", "parameters": {"jq_expression": ".qwe", "drop_attributes": True}},
            ),
        ],
    )
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_create(self, form_data, fields_to_check, create_aux_objects):
        form = forms.SerializerForm(data=form_data)
        assert form.is_valid(), form.errors
        form.save()
        instance = models.Serializer.objects.get()
        self._check_fields(instance, fields_to_check)

    @pytest.mark.parametrize(
        "form_data, errored_fields",
        [
            ({"name": "s", "extraction_method": "TTP"}, {"template"}),
            ({"name": "s", "extraction_method": "TTP", "template": "q", "data_source": "1"}, {"__all__"}),
            ({"name": "s", "extraction_method": "YAML", "jq_expression": "((("}, {"jq_expression"}),
        ],
    )
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_create_invalid(self, form_data, errored_fields, create_aux_objects):
        form = forms.SerializerForm(data=form_data)
        assert not form.is_valid()
        assert form.errors.keys() == errored_fields

    @pytest.mark.parametrize(
        "factory, form_data, fields_to_check",
        [
            (
                pt(SerializerDBFactory, extraction_method="TEXTFSM", template="qwerty"),
                {"name": "s", "extraction_method": "XML", "drop_attributes": "true"},
                {
                    "template": "",
                    "extraction_method": "XML",
                    "parameters": {"jq_expression": "", "drop_attributes": True},
                },
            ),
            (
                pt(SerializerDSFactory, extraction_method="TEXTFSM"),
                {"name": "s", "extraction_method": "ROUTEROS"},
                {"template": "", "data_source": None, "data_file": None},
            ),
            (
                pt(SerializerDBFactory, extraction_method="ROUTEROS", template=""),
                {"name": "s", "extraction_method": "TTP", "template": "qwe"},
                {"template": "qwe"},
            ),
        ],
    )
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_update(self, factory, form_data, fields_to_check, create_aux_objects):
        instance = factory()
        form = forms.SerializerForm(data=form_data, instance=instance)
        assert form.is_valid(), form.errors
        form.save()
        instance.refresh_from_db()
        self._check_fields(instance, fields_to_check)
