from typing import Annotated, Any

from django.contrib import messages
from django.forms import Form
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView
from utilities.rqworker import get_workers_for_queue

from validity import di
from validity.forms import RunTestsForm
from validity.scripts.data_models import RunTestsParams, ScriptParams
from validity.scripts.launch import Launcher


class RunScriptView(FormView):
    template_name = "validity/script_run.html"
    redirect_viewname = "extras:script_result"
    params_class: type[ScriptParams]
    launcher: Launcher

    def get_params(self, form: Form):
        params = {key: value for key in form.data if (value := form.data[key]) != ""}
        return self.params_class(request=self.request, **params)

    def get_success_url(self, job_id: int) -> str:
        return reverse(self.redirect_viewname, kwargs={"job_pk": job_id})

    def form_valid(self, form: Form) -> HttpResponse:
        if not get_workers_for_queue(queue_name := self.launcher.rq_queue.name):
            messages.error(
                self.request, _("Unable to run script: no running RQ worker found for the queue %s").format(queue_name)
            )
            return self.render_to_response(self.get_context_data())
        job = self.launcher(self.get_params(form))
        return HttpResponseRedirect(self.get_success_url(job.pk))


class RunTestsView(RunScriptView):
    params_class = RunTestsParams
    form_class = RunTestsForm

    @di.inject
    def __init__(self, launcher: Annotated[Launcher, "runtests_launcher"], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.launcher = launcher
