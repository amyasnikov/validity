from functools import partial
from http import HTTPStatus

import pytest
from factories import DeviceFactory, ReportFactory, SelectorFactory
from factory.django import DjangoModelFactory


class GraphQLTest:
    query: str
    factory: type[DjangoModelFactory] | list[type]
    subanswer: dict | None
    data_name: str

    @pytest.mark.django_db
    def test_query(self, gql_query):
        factories = self.factory if isinstance(self.factory, list) else [self.factory]
        for factory in factories:
            factory()
        resp = gql_query(self.query)
        assert resp.status_code == HTTPStatus.OK
        if self.subanswer is None:
            return
        answer = resp.json()["data"][self.data_name]
        if isinstance(answer, list):
            answer = answer[0]
        assert self.subanswer.items() <= answer.items()


class TestReportList(GraphQLTest):
    query = """
    query {
        report_list {
            id
            device_count
            test_count
            total_passed
            total_count
            low_passed
            low_count
            middle_passed
            middle_count
            high_passed
            high_count
        }
    }
    """
    factory = partial(ReportFactory, passed_results=3, failed_results=5)
    subanswer = {
        "device_count": 8,
        "test_count": 8,
        "total_passed": 3,
        "total_count": 8,
        "low_passed": 0,
        "low_count": 0,
        "middle_passed": 3,
        "middle_count": 8,
        "high_passed": 0,
        "high_count": 0,
    }
    data_name = "report_list"


class TestSelector(GraphQLTest):
    query = """
    query {
        selector (id: 1) {
            name
            devices {
                name
            }
        }
    }
    """
    factory = [
        partial(SelectorFactory, name_filter="dev.*", id=1, name="selector1"),
        partial(DeviceFactory, name="dev1"),
        partial(DeviceFactory, name="dev2"),
        partial(DeviceFactory, name="qwerty"),
    ]
    subanswer = {"name": "selector1", "devices": [{"name": "dev1"}, {"name": "dev2"}]}
    data_name = "selector"
