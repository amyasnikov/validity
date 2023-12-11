from .command import CommandBulkDeleteView, CommandDeleteView, CommandEditView, CommandListView, CommandView
from .device import DeviceSerializedConfigView, TestResultView
from .nameset import NameSetBulkDeleteView, NameSetDeleteView, NameSetEditView, NameSetListView, NameSetView
from .poller import PollerBulkDeleteView, PollerDeleteView, PollerEditView, PollerListView, PollerView
from .report import ComplianceReportListView, ComplianceReportView
from .selector import (
    ComplianceSelectorBulkDeleteView,
    ComplianceSelectorDeleteView,
    ComplianceSelectorEditView,
    ComplianceSelectorListView,
    ComplianceSelectorView,
)
from .serializer import (
    ConfigSerializerBulkDeleteView,
    ConfigSerializerDeleteView,
    ConfigSerializerEditView,
    ConfigSerializerListView,
    ConfigSerializerView,
)
from .test import (
    ComplianceTestBulkDeleteView,
    ComplianceTestDeleteView,
    ComplianceTestEditView,
    ComplianceTestListView,
    ComplianceTestView,
)
from .test_result import ComplianceResultListView, ComplianceResultView
