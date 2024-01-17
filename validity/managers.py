from functools import partialmethod
from itertools import chain

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    BigIntegerField,
    BooleanField,
    Case,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Prefetch,
    Q,
    Value,
    When,
)
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from netbox.models import RestrictedQuerySet

from validity import settings
from validity.choices import DeviceGroupByChoices, SeverityChoices
from validity.utils.orm import CustomPrefetchMixin, SetAttributesMixin


class ComplianceTestQS(RestrictedQuerySet):
    def pf_latest_results(self) -> "ComplianceTestQS":
        from validity.models import ComplianceTestResult

        return self.prefetch_related(Prefetch("results", ComplianceTestResult.objects.only_latest()))

    def annotate_latest_count(self):
        from validity.models import ComplianceTestResult

        return self.annotate(
            passed=Count(
                "results",
                distinct=True,
                filter=Q(results__passed=True, results__in=ComplianceTestResult.objects.only_latest()),
            ),
            failed=Count(
                "results",
                distinct=True,
                filter=Q(results__passed=False, results__in=ComplianceTestResult.objects.only_latest()),
            ),
        )


class ComplianceTestResultQS(RestrictedQuerySet):
    def only_latest(self, exclude: bool = False) -> "ComplianceTestResultQS":
        qs = self.order_by("test__pk", "device__pk", "-created").distinct("test__pk", "device__pk")
        if exclude:
            return self.exclude(pk__in=qs.values("pk"))
        return self.filter(pk__in=qs.values("pk"))

    def last_more_than(self, than: int) -> "ComplianceTestResultQS":
        qs = self.values("device", "test").annotate(ids=ArrayAgg(F("id"), ordering="-created"))
        last_ids = chain.from_iterable(record["ids"][than:] for record in qs.iterator())
        return self.filter(pk__in=last_ids)

    def count_devices_and_tests(self):
        return self.aggregate(device_count=Count("devices", distinct=True), test_count=Count("tests", distinct=True))

    def delete_old(self, _settings=settings):
        del_count = self.filter(report=None).last_more_than(_settings.store_last_results)._raw_delete(self.db)
        return (del_count, {"validity.ComplianceTestResult": del_count})


def percentage(field1: str, field2: str) -> Case:
    return Case(
        When(Q(**{f"{field2}__gt": 0}), then=Value(100.0) * F(field1) / F(field2)),
        default=100.0,
        output_field=FloatField(),
    )


class VDataFileQS(RestrictedQuerySet):
    pass


class VDataSourceQS(CustomPrefetchMixin, RestrictedQuerySet):
    def annotate_config_path(self):
        return self.annotate(device_config_path=KeyTextTransform("device_config_path", "custom_field_data"))

    def annotate_command_path(self):
        return self.annotate(device_command_path=KeyTextTransform("device_command_path", "custom_field_data"))

    def annotate_paths(self):
        return self.annotate_config_path().annotate_command_path()


class ComplianceReportQS(RestrictedQuerySet):
    def annotate_result_stats(self, groupby_field: DeviceGroupByChoices | None = None):
        qs = self
        if groupby_field:
            qs = self.values(f"results__{groupby_field.pk_field()}", f"results__{groupby_field}")
        only_passed = Q(results__passed=True)
        qs = qs.annotate(
            total_count=Count("results"),
            total_passed=Count("results", filter=only_passed),
            total_percentage=percentage("total_passed", "total_count"),
        )
        for severity, _ in SeverityChoices.choices:
            s_lower = severity.lower()
            s_filter = Q(results__test__severity=severity)
            qs = qs.annotate(
                **{
                    f"{s_lower}_count": Count("results", filter=s_filter),
                    f"{s_lower}_passed": Count("results", filter=s_filter & only_passed),
                    f"{s_lower}_percentage": percentage(f"{s_lower}_passed", f"{s_lower}_count"),
                }
            )
        return qs

    def count_devices_and_tests(self):
        return self.annotate(
            device_count=Count("results__device", distinct=True), test_count=Count("results__test", distinct=True)
        )

    def delete_old(self, _settings=settings):
        from validity.models import ComplianceTestResult

        old_reports = list(self.order_by("-created").values_list("pk", flat=True)[_settings.store_reports :])
        deleted_results = ComplianceTestResult.objects.filter(report__pk__in=old_reports)._raw_delete(self.db)
        deleted_reports, _ = self.filter(pk__in=old_reports).delete()
        return (
            deleted_results + deleted_reports,
            {"validity.ComplianceTestResult": deleted_results, "validity.ComplianceReport": deleted_reports},
        )


class VDeviceQS(CustomPrefetchMixin, SetAttributesMixin, RestrictedQuerySet):
    def set_selector(self, selector):
        return self.set_attribute("selector", selector)

    def set_datasource(self, data_source):
        return self.set_attribute("data_source", data_source)

    def annotate_datasource_id(self):
        from validity.models import VDataSource

        return self.annotate(
            bound_source=Cast(KeyTextTransform("data_source", "tenant__custom_field_data"), BigIntegerField())
        ).annotate(
            data_source_id=Case(
                When(bound_source__isnull=False, then=F("bound_source")),
                default=VDataSource.objects.filter(custom_field_data__default=True).values("id")[:1],
                output_field=BigIntegerField(),
            )
        )

    def prefetch_datasource(self, prefetch_config_files: bool = False):
        from validity.models import VDataSource

        datasource_qs = VDataSource.objects.all()
        if prefetch_config_files:
            datasource_qs = datasource_qs.prefetch_config_files()
        return self.annotate_datasource_id().custom_prefetch("data_source", datasource_qs)

    def annotate_cf(self, cf: str, annotation: str = ""):
        """
        Annotates CF value (in decreasing precedence):
            1) From device itself
            2) from device type
            3) from manufacturer
        """
        annotation = annotation or cf
        device_cf = f"device_{cf}"
        devtype_cf = f"devtype_{cf}"
        manuf_cf = f"manuf_{cf}"
        return (
            self.annotate(**{device_cf: KeyTextTransform(cf, "custom_field_data")})
            .annotate(
                **{devtype_cf: KeyTextTransform(cf, "device_type__custom_field_data")},
            )
            .annotate(**{manuf_cf: KeyTextTransform(cf, "device_type__manufacturer__custom_field_data")})
            .annotate(
                **{
                    annotation: Case(
                        When(**{f"{device_cf}__isnull": False, "then": Cast(F(device_cf), BigIntegerField())}),
                        When(**{f"{devtype_cf}__isnull": False, "then": Cast(F(devtype_cf), BigIntegerField())}),
                        When(**{f"{manuf_cf}__isnull": False, "then": Cast(F(manuf_cf), BigIntegerField())}),
                    )
                }
            )
        )

    annotate_serializer_id = partialmethod(annotate_cf, "serializer", "serializer_id")
    annotate_poller_id = partialmethod(annotate_cf, "poller", "poller_id")

    def prefetch_serializer(self):
        from validity.models import Serializer

        return self.annotate_serializer_id().custom_prefetch(
            "serializer", Serializer.objects.select_related("data_file")
        )

    def prefetch_poller(self, with_commands: bool = False):
        from validity.models import Poller

        poller_qs = Poller.objects.all()
        if with_commands:
            poller_qs = poller_qs.prefetch_commands()
        return self.annotate_poller_id().custom_prefetch("poller", poller_qs)

    def _count_per_something(self, field: str, annotate_method: str) -> dict[int | None, int]:
        qs = getattr(self, annotate_method)().values(field).annotate(cnt=Count("id", distinct=True))
        result = {}
        for values in qs:
            result[values[field]] = values["cnt"]
        return result

    count_per_serializer = partialmethod(_count_per_something, "serializer_id", "annotate_serializer_id")
    count_per_poller = partialmethod(_count_per_something, "poller_id", "annotate_poller_id")

    def annotate_result_stats(self, report_id: int, severity_ge: SeverityChoices = SeverityChoices.LOW):
        results_filter = Q(results__report__pk=report_id) & self._severity_filter(severity_ge, "results")
        return self.annotate(
            results_count=Count("results", filter=results_filter),
            results_passed=Count("results", filter=results_filter & Q(results__passed=True)),
            results_percentage=percentage("results_passed", "results_count"),
            compliance_passed=ExpressionWrapper(Q(results_count=F("results_passed")), output_field=BooleanField()),
        )

    @staticmethod
    def _severity_filter(severity: SeverityChoices, query_base: str = "") -> Q:
        query_path = "test__severity__in"
        if query_base:
            query_path = f"{query_base}__{query_path}"
        return Q(**{query_path: SeverityChoices.ge(severity)})

    def prefetch_results(self, report_id: int, severity_ge: SeverityChoices = SeverityChoices.LOW):
        from validity.models import ComplianceTestResult

        return self.prefetch_related(
            Prefetch(
                "results",
                queryset=ComplianceTestResult.objects.filter(self._severity_filter(severity_ge), report__pk=report_id)
                .select_related("test")
                .order_by("test__name"),
            )
        )


class PollerQS(RestrictedQuerySet):
    def prefetch_commands(self):
        Command = self.model._meta.get_field("commands").remote_field.model
        return self.prefetch_related(Prefetch("commands", Command.objects.order_by("-retrieves_config")))


class CommandQS(CustomPrefetchMixin, SetAttributesMixin, RestrictedQuerySet):
    def set_file_paths(self, device, data_source):
        """
        Sets up 'path' attribute to each command
        """
        self.set_attribute("device", device)
        self.set_attribute("data_source", data_source)
        return self

    def bind_attributes(self, instance):
        initial_attrs = self._aux_attributes.copy()
        device = self._aux_attributes.pop("device", None)
        data_source = self._aux_attributes.pop("data_source", None)
        if device and data_source:
            path = data_source.get_command_path(device, instance)
            instance.path = path
        super().bind_attributes(instance)
        self._aux_attributes = initial_attrs
