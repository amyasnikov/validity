from .device import DeviceSerializedConfigView, TestResultView
from .keybundle import KeyBundleBulkDeleteView, KeyBundleDeleteView, KeyBundleEditView, KeyBundleListView, KeyBundleView
from .nameset import NameSetBulkDeleteView, NameSetDeleteView, NameSetEditView, NameSetListView, NameSetView
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
