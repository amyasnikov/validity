from functools import partial as p

import pytest
from factories import (
    CompTestDBFactory,
    CompTestDSFactory,
    NameSetDBFactory,
    NameSetDSFactory,
    SerializerDBFactory,
    SerializerDSFactory,
)


@pytest.mark.parametrize(
    "factory, prop_name, expected_value",
    [
        (p(SerializerDBFactory, template="template"), "effective_template", "template"),
        (p(SerializerDSFactory, contents="template2"), "effective_template", "template2"),
        (p(NameSetDBFactory, definitions="def f(): pass"), "effective_definitions", "def f(): pass"),
        (p(NameSetDSFactory, contents="def f2(): pass"), "effective_definitions", "def f2(): pass"),
        (p(CompTestDBFactory, expression="1==2"), "effective_expression", "1==2"),
        (p(CompTestDSFactory, contents="1==3"), "effective_expression", "1==3"),
    ],
)
@pytest.mark.django_db
def test_git_link_model(factory, prop_name, expected_value):
    created_model = factory()
    obj = type(created_model).objects.filter(pk=created_model.pk).first()
    assert getattr(obj, prop_name) == expected_value
