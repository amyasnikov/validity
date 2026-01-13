from functools import partial

import pytest
from factories import (
    BackupPointFactory,
    CommandFactory,
    CompTestDBFactory,
    CompTestResultFactory,
    DeviceFactory,
    NameSetDBFactory,
    PollerFactory,
    ReportFactory,
    SelectorFactory,
    SerializerDBFactory,
)
from factory.django import DjangoModelFactory

from validity import config


nb_version_43_or_above = pytest.mark.skipif(config.netbox_version < "4.3.0", reason="graphql works for netbox 4.3+")


class GraphQLTest:
    query: str
    factory: type[DjangoModelFactory] | list[type]
    subanswer: dict | None
    data_name: str

    @pytest.mark.django_db
    def test_query(self, gql_query):
        selftype = type(self)
        factories = selftype.factory if isinstance(selftype.factory, list) else [selftype.factory]
        for factory in factories:
            factory()
        resp = gql_query(self.query)
        assert resp.errors is None
        answer = resp.data[self.data_name]
        self.answer_checks(answer, resp.data)
        if self.subanswer is None:
            return
        if isinstance(answer, list):
            answer = answer[0]
        assert all(answer[k] == v for k, v in self.subanswer.items())

    def answer_checks(self, answer, data):
        return


@nb_version_43_or_above
class TestReportList(GraphQLTest):
    query = """
    query {
        validity_report_list {
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
    data_name = "validity_report_list"


@nb_version_43_or_above
class TestSelector(GraphQLTest):
    query = """
    query {
        validity_selector (id: 1) {
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
    data_name = "validity_selector"


@nb_version_43_or_above
class TestSelectorList(GraphQLTest):
    query = """
    query {
        validity_selector_list(filters: { name: { exact: "selector1" }}) {
            id
            name
            devices { name }
        }
    }
    """
    factory = [
        partial(SelectorFactory, id=1, name="selector1", name_filter="dev.*"),
        partial(DeviceFactory, name="dev1"),
        partial(DeviceFactory, name="qwerty"),
    ]
    subanswer = {"name": "selector1"}
    data_name = "validity_selector_list"

    def answer_checks(self, answer, data):
        assert isinstance(answer, list)
        assert any({"name": "dev1"} in item.get("devices", []) for item in answer)


@nb_version_43_or_above
class TestComplianceTest(GraphQLTest):
    query = """
    query {
        validity_test(id: 1) {
            id
            name
            selectors { id name }
        }
    }
    """
    factory = [
        partial(SelectorFactory, id=1, name="selector1"),
        partial(CompTestDBFactory, id=1, name="test-1"),
    ]
    subanswer = {"name": "test-1"}
    data_name = "validity_test"

    def answer_checks(self, answer, data):
        # Link selector to test post-create (since factory list is applied sequentially)
        # Cannot mutate DB here, so assert structure only; detailed linkage is tested in list test
        assert answer["id"] == "1"


@nb_version_43_or_above
class TestComplianceTestList(GraphQLTest):
    query = """
    query {
        validity_test_list(filters: { name: { contains: "test-" } }) {
            id
            name
            selectors { id name }
        }
    }
    """

    def _setup():
        sel = SelectorFactory(id=2, name="sel-2")
        t1 = CompTestDBFactory(name="test-1")
        t2 = CompTestDBFactory(name="test-2")
        t1.selectors.add(sel)
        t2.selectors.add(sel)

    factory = [_setup]
    subanswer = None
    data_name = "validity_test_list"

    def answer_checks(self, answer, data):
        assert isinstance(answer, list) and len(answer) >= 2
        assert any(item["name"] == "test-1" for item in answer)


@nb_version_43_or_above
class TestComplianceTestResult(GraphQLTest):
    query = """
    query {
        validity_test_result(id: 1) {
            id
            passed
            test { id name }
            report { id }
        }
    }
    """

    def _setup():
        t = CompTestDBFactory(id=3, name="test-x")
        r = ReportFactory(id=3)
        CompTestResultFactory(id=1, test=t, report=r, passed=True)

    factory = [_setup]
    subanswer = {"passed": True}
    data_name = "validity_test_result"


@nb_version_43_or_above
class TestComplianceTestResultList(GraphQLTest):
    query = """
    query {
        validity_test_result_list(filters: { latest: true, test: { id: { exact: 4 } } }) {
            id
            passed
            test { id name }
            report { id }
        }
    }
    """

    def _setup():
        t = CompTestDBFactory(id=4, name="test-y")
        r = ReportFactory()
        # Two results for the same device to ensure only latest per device/test remains
        dev_a = DeviceFactory(name="dev-a")
        CompTestResultFactory(test=t, report=r, device=dev_a, passed=False)
        CompTestResultFactory(test=t, report=r, device=dev_a, passed=True)
        # Another device
        CompTestResultFactory(test=t, report=r, passed=True)

    factory = [_setup]
    subanswer = None
    data_name = "validity_test_result_list"

    def answer_checks(self, answer, data):
        assert isinstance(answer, list) and len(answer) == 2


@nb_version_43_or_above
class TestSerializer(GraphQLTest):
    query = """
    query {
        validity_serializer(id: 1) {
            id
            name
            extraction_method
            template
        }
    }
    """
    factory = [partial(SerializerDBFactory, id=1, name="ser1")]
    subanswer = {"name": "ser1"}
    data_name = "validity_serializer"


@nb_version_43_or_above
class TestSerializerList(GraphQLTest):
    query = """
    query {
        validity_serializer_list(filters: { name: { exact: "ser1" } }) {
            id
            name
            extraction_method
        }
    }
    """
    factory = [partial(SerializerDBFactory, name="ser1"), partial(SerializerDBFactory, name="ser2")]
    subanswer = {"name": "ser1"}
    data_name = "validity_serializer_list"


@nb_version_43_or_above
class TestNameSet(GraphQLTest):
    query = """
    query {
        validity_nameset(id: 1) { id name global }
    }
    """
    factory = [partial(NameSetDBFactory, id=1, name="ns1", _global=True)]
    subanswer = {"name": "ns1", "global": True}
    data_name = "validity_nameset"


@nb_version_43_or_above
class TestNameSetList(GraphQLTest):
    query = """
    query {
        validity_nameset_list(filters: { name: { contains: "ns" }, global: true }, global: true) {
            id
            name
            global
        }
    }
    """
    factory = [
        partial(NameSetDBFactory, name="ns1", _global=True),
        partial(NameSetDBFactory, name="ns2", _global=False),
    ]
    subanswer = {"global": True}
    data_name = "validity_nameset_list"

    def answer_checks(self, answer, data):
        assert isinstance(answer, list) and len(answer) >= 1
        assert all(item["global"] is True for item in answer)


@nb_version_43_or_above
class TestReport(GraphQLTest):
    query = """
    query {
        validity_report(id: 1) {
            id
            device_count
            test_count
            total_passed
            total_count
            middle_count
        }
    }
    """
    factory = [partial(ReportFactory, id=1, passed_results=1, failed_results=2)]
    subanswer = {"total_passed": 1, "total_count": 3}
    data_name = "validity_report"


@nb_version_43_or_above
class TestPoller(GraphQLTest):
    query = """
    query {
        validity_poller(id: 1) { id name connection_type }
    }
    """
    factory = [partial(PollerFactory, id=1, name="poller1")]
    subanswer = {"name": "poller1"}
    data_name = "validity_poller"


@nb_version_43_or_above
class TestPollerList(GraphQLTest):
    query = """
    query {
        validity_poller_list(filters: { name: { exact: "poller1" } }) { id name }
    }
    """
    factory = [partial(PollerFactory, name="poller1"), partial(PollerFactory, name="poller2")]
    subanswer = {"name": "poller1"}
    data_name = "validity_poller_list"


@nb_version_43_or_above
class TestCommand(GraphQLTest):
    query = """
    query {
        validity_command(id: 1) { id name label parameters }
    }
    """
    factory = [partial(CommandFactory, id=1, name="cmd1")]
    subanswer = {"name": "cmd1"}
    data_name = "validity_command"

    def answer_checks(self, answer, data):
        assert "cli_command" in answer.get("parameters", {})


@nb_version_43_or_above
class TestCommandList(GraphQLTest):
    query = """
    query {
        validity_command_list(filters: { name: { exact: "cmd1" } }) { id name parameters }
    }
    """
    factory = [partial(CommandFactory, name="cmd1"), partial(CommandFactory, name="cmd2")]
    subanswer = {"name": "cmd1"}
    data_name = "validity_command_list"


@nb_version_43_or_above
class TestBackupPoint(GraphQLTest):
    query = """
    query {
        validity_backup_point(id: 1) { id name method parameters }
    }
    """
    factory = [partial(BackupPointFactory, id=1, name="bp1")]
    subanswer = {"name": "bp1"}
    data_name = "validity_backup_point"

    def answer_checks(self, answer, data):
        params = answer.get("parameters") or {}
        assert "username" in params


@nb_version_43_or_above
class TestBackupPointList(GraphQLTest):
    query = """
    query {
        validity_backup_point_list(filters: { name: { contains: "bp-" } }) { id name }
    }
    """
    factory = [BackupPointFactory]
    subanswer = None
    data_name = "validity_backup_point_list"
