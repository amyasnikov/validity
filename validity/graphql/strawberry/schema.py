from typing import Annotated, List

import strawberry
import strawberry_django
from netbox.graphql.types import NetBoxObjectType

from validity import models
from validity.graphql.strawberry import filters


@strawberry_django.type(
    models.NameSet,
    filters=filters.NameSetFilter,
    fields="__all__",
)
class NameSetType(NetBoxObjectType):
    tests: List[Annotated["ComplianceTestType", strawberry.lazy("validity.graphql.strawberry.schema")]]
    _global: strawberry.auto = strawberry_django.field(name="global")


@strawberry_django.type(models.ComplianceTest, filters=filters.ComplianceTestFilter, fields="__all__")
class ComplianceTestType(NetBoxObjectType):
    pass


@strawberry.type
class Query:
    @strawberry.field
    def nameset(self, id: int) -> NameSetType:
        return models.NameSet.objects.get(pk=id)

    nameset_list: list[NameSetType] = strawberry_django.field()

    @strawberry.field
    def test(self, id: int) -> NameSetType:
        return models.ComplianceTest.objects.get(pk=id)

    test_list: list[ComplianceTestType] = strawberry_django.field()


schema = Query
