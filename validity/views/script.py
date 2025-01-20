from typing import Annotated, Any

from core.models import Job
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import FormView
from netbox.views.generic import ObjectView
from netbox.views.generic.mixins import TableMixin
from utilities.htmx import htmx_partial

from validity import di
from validity.forms import RunTestsForm
from validity.scripts import Launcher, RunTestsParams, ScriptParams
from validity.tables import ScriptResultTable
from .base import LauncherMixin


class RunScriptView(LauncherMixin, PermissionRequiredMixin, FormView):
    template_name = "validity/scripts/run.html"
    params_class: type[ScriptParams]
    empty_form_values = ("", None)

    def get_params(self, form: Form):
        form_data = {field: value for field, value in form.cleaned_data.items() if value not in self.empty_form_values}
        return self.params_class(request=self.request, **form_data)

    def form_valid(self, form: Form) -> HttpResponse:
        params = self.get_params(form)
        return self.launch_or_render_error(params)


class RunTestsView(RunScriptView):
    params_class = RunTestsParams
    form_class = RunTestsForm
    permission_required = "validity.run_compliancetest"

    @di.inject
    def __init__(self, launcher: Annotated[Launcher, "runtests_launcher"], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.launcher = launcher


class ScriptResultView(PermissionRequiredMixin, TableMixin, ObjectView):
    queryset = Job.objects.filter(object_type__app_label="validity")
    table_class = ScriptResultTable
    template_name = "validity/scripts/result.html"
    htmx_template_name = "validity/scripts/result_htmx.html"
    permission_required = "core.view_job"

    def get_table(self, job, request, bulk_actions=False):
        logs = [entry | {"index": i} for i, entry in enumerate(job.data["log"], start=1)]
        table = self.table_class(logs, user=request.user)
        table.configure(request)
        return table

    def get(self, request, **kwargs):
        job = self.get_object(**kwargs)
        table = self.get_table(job, request) if job.completed else None
        context = {"job": job, "table": table}
        if htmx_partial(request):
            response = render(request, self.htmx_template_name, context)
            if job.completed or not job.started:
                response.status_code = 286  # cancel HTMX polling
            return response

        return render(request, self.template_name, context)
