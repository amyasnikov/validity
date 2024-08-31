from typing import Annotated, Any

from core.models import Job
from django.contrib import messages
from django.forms import Form
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView
from netbox.views.generic import ObjectView
from netbox.views.generic.mixins import TableMixin

from validity import di
from validity.forms import RunTestsForm
from validity.netbox_changes import htmx_partial
from validity.scripts.data_models import RunTestsParams, ScriptParams
from validity.scripts.launch import Launcher
from validity.tables import ScriptResultTable


class RunScriptView(FormView):
    template_name = "validity/scripts/run.html"
    redirect_viewname = "plugins:validity:script_result"
    params_class: type[ScriptParams]
    empty_form_values = ("", None)

    # these params must be injected into __init__
    launcher: Launcher
    worker_count: int

    def get_params(self, form: Form):
        form_data = {field: value for field, value in form.cleaned_data.items() if value not in self.empty_form_values}
        return self.params_class(request=self.request, **form_data)

    def get_success_url(self, job_id: int) -> str:
        return reverse(self.redirect_viewname, kwargs={"pk": job_id})

    def form_valid(self, form: Form) -> HttpResponse:
        if self.worker_count == 0:
            messages.error(
                self.request,
                _('Unable to run script: no running RQ worker found for the queue "{}"').format(
                    self.launcher.rq_queue.name
                ),
            )
            return self.render_to_response(self.get_context_data())
        job = self.launcher(self.get_params(form))
        return HttpResponseRedirect(self.get_success_url(job.pk))


class RunTestsView(RunScriptView):
    params_class = RunTestsParams
    form_class = RunTestsForm

    @di.inject
    def __init__(
        self,
        launcher: Annotated[Launcher, "runtests_launcher"],
        worker_count: Annotated[int, "runtests_worker_count"],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.launcher = launcher
        self.worker_count = worker_count


class ScriptResultView(TableMixin, ObjectView):
    queryset = Job.objects.filter(object_type__model="compliancereport", object_type__app_label="validity")
    table_class = ScriptResultTable
    template_name = "validity/scripts/result.html"
    htmx_template_name = "validity/scripts/result_htmx.html"

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
