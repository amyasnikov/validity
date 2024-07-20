from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from typing import Any, Callable, ContextManager, Iterable, Iterator

from django.db.models import Prefetch, QuerySet

from validity import settings
from validity.compliance.exceptions import EvalError, SerializationError
from validity.models import ComplianceSelector, ComplianceTest, ComplianceTestResult, NameSet, VDataSource, VDevice
from validity.utils.orm import TwoPhaseTransaction
from ..data_models import ExecutionResult, FullScriptParams, TestResultRatio
from ..logger import Logger
from ..parent_jobs import JobExtractor


class TestExecutor:
    """
    Executes all the tests for specified subset of devices
    """

    def __init__(self, worker_id: int, explanation_verbosity: int, report_id: int) -> None:
        self.explanation_verbosity = explanation_verbosity
        self.report_id = report_id
        self.settings = settings
        self.log = Logger(script_id=f"Worker {worker_id}")
        self.results_count = 0
        self.results_passed = 0
        self._nameset_functions = {}
        self.global_namesets = NameSet.objects.filter(_global=True)

    def nameset_functions(self, namesets: Iterable[NameSet]) -> dict[str, Callable]:
        result = {}
        for nameset in chain(namesets, self.global_namesets):
            if nameset.name not in self._nameset_functions:
                try:
                    new_functions = nameset.extract()
                except Exception as e:
                    self.log.warning(f"Cannot extract code from nameset {nameset}, {type(e).__name__}: {e}")
                    new_functions = {}
                self._nameset_functions[nameset.name] = new_functions
            result |= self._nameset_functions[nameset.name]
        return result

    def run_test(self, device: VDevice, test: ComplianceTest) -> tuple[bool, list[tuple[Any, Any]]]:
        functions = self.nameset_functions(test.namesets.all())
        return test.run(device, functions, verbosity=self.explanation_verbosity)

    def run_tests_for_device(
        self,
        tests_qs: QuerySet[ComplianceTest],
        device: VDevice,
    ) -> Iterator[ComplianceTestResult]:
        for test in tests_qs:
            explanation = []
            try:
                device.state  # noqa: B018
                passed, explanation = self.run_test(device, test)
            except EvalError as exc:
                self.log.failure(f"Failed to execute test **{test}** for device **{device}**, `{exc}`")
                passed = False
                explanation.append((str(exc), None))
            self.results_count += 1
            self.results_passed += int(passed)
            yield ComplianceTestResult(
                test=test,
                device=device,
                passed=passed,
                explanation=explanation,
                report=self.report_id,
                dynamic_pair=device.dynamic_pair,
            )

    def __call__(self, devices: QuerySet[VDevice], tests: QuerySet[ComplianceTest]) -> Iterator[ComplianceTestResult]:
        for device in devices:
            try:
                yield from self.run_tests_for_device(tests, device)
            except SerializationError as e:
                self.log.failure(f"`{e}`, ignoring all tests for *{device}*")
                continue


class DeviceTestIterator:
    """
    Generates pairs of (devices, tests) where each test has to be executed on each of the corresponding devices
    """

    def __init__(
        self, selector_devices: dict[int, list[int]], test_tags: list[int], override_datasource_id: int | None
    ):
        self.selector_devices = selector_devices
        self.test_tags = test_tags
        self.override_datasource_id = override_datasource_id
        self.all_selectors = self._get_selectors().in_bulk()

    def __iter__(self):
        return self

    def __next__(self):
        if not self.selector_devices:
            raise StopIteration
        selector_id, device_ids = self.selector_devices.popitem()
        selector = self.all_selectors[selector_id]
        devices = self._get_device_qs(selector, device_ids)
        return devices, selector.tests.all()

    @cached_property
    def override_datasource(self) -> VDataSource | None:
        if self.override_datasource_id:
            return VDataSource.objects.get(pk=self.override_datasource_id)

    def _get_selectors(self):
        selectors = ComplianceSelector.objects.all()
        test_qs = ComplianceTest.objects.all()
        if self.test_tags:
            test_qs = test_qs.filter(tags__pk__in=self.test_tags).distinct()
        return selectors.prefetch_related(Prefetch("tests", test_qs.prefetch_related("namesets")))

    def _get_device_qs(self, selector: ComplianceSelector, device_ids: list[int]) -> QuerySet[VDevice]:
        device_qs = selector.devices.select_related().prefetch_serializer().prefetch_poller()
        if self.override_datasource:
            device_qs = device_qs.set_datasource(self.override_datasource)
        else:
            device_qs = device_qs.prefetch_datasource()
        device_qs = device_qs.filter(pk__in=device_ids)
        return device_qs


@dataclass
class ApplyWorker:
    """
    Provides a function to execute specified tests, save the results to DB and return ExecutionResult
    """

    test_executor_cls: type[TestExecutor]
    device_test_gen: type[DeviceTestIterator]
    result_batch_size: int
    job_extractor_factory: Callable[[], JobExtractor]
    prepare_transaction: Callable[[str], ContextManager]
    transaction_template: str

    def __call__(self, params: FullScriptParams, worker_id: int) -> ExecutionResult:
        selector_devices = self.get_selector_devices(worker_id)
        executor = self.test_executor_cls(worker_id, params.explanation_verbosity, params.report_id)
        test_results = (
            executor(devices, tests)
            for devices, tests in self.device_test_gen(selector_devices, params.test_tags, params.override_datasource)
        )
        chained_results = chain.from_iterable(test_results)
        self.save_results_to_db(chained_results, params.job_id, worker_id)
        return ExecutionResult(TestResultRatio(executor.results_passed, executor.results_count), executor.log.messages)

    def get_selector_devices(self, worker_id: int) -> dict[int, list[int]]:
        job_extractor = self.job_extractor_factory()
        return job_extractor.parent.job.result[worker_id]

    def save_results_to_db(self, results: Iterable[ComplianceTestResult], job_id: int, worker_id: int) -> None:
        transaction_id = self.transaction_template.format(job=job_id, worker=worker_id)
        with self.prepare_transaction(transaction_id):
            ComplianceTestResult.objects.bulk_create(results, batch_size=self.result_batch_size)


execute_tests = ApplyWorker(
    test_executor_cls=TestExecutor,
    device_test_gen=DeviceTestIterator,
    result_batch_size=settings.result_batch_size,
    job_extractor_factory=JobExtractor,
    prepare_transaction=lambda transaction_id: TwoPhaseTransaction(transaction_id).prepare(),
    transaction_template="ApplyWorker_{job}_{worker}",
)