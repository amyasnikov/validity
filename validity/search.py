from netbox.search import SearchIndex, register_search

from validity import models


@register_search
class NameSetIndex(SearchIndex):
    model = models.NameSet
    fields = (("name", 100), ("description", 500), ("definitions", 1000))


@register_search
class SelectorIndex(SearchIndex):
    model = models.ComplianceSelector
    fields = (
        ("name", 100),
        ("name_filter", 200),
    )


@register_search
class SerializerIndex(SearchIndex):
    model = models.ConfigSerializer
    fields = (
        ("name", 100),
        ("ttp_template", 1000),
    )


@register_search
class TestIndex(SearchIndex):
    model = models.ComplianceTest
    fields = (("name", 100), ("expression", 1000))
