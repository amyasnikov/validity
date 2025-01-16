from typing import Any, Dict

from django.contrib import messages
from django.db.models import Model
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as __
from django_filters import FilterSet
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, Table
from utilities.views import ObjectPermissionRequiredMixin as _ObjectPermissionRequiredMixin
from utilities.views import ViewTab

from validity import filtersets, forms, models, scripts, tables
from validity.utils.misc import partialcls


class ObjectPermissionRequiredMixin(_ObjectPermissionRequiredMixin):
    permission_required: str

    def get_required_permission(self):
        return self.permission_required


class TableMixin:
    """
    Mixin to filter aux table in DetailView
    """

    object_table_field: str
    filterset: type[FilterSet]
    table: type[Table]

    def get_table_qs(self, request, instance):
        return getattr(instance, self.object_table_field).all()

    def get_table_data(self, request, instance):
        qs = self.get_table_qs(request, instance)
        return self.filterset(request.GET, qs, request=request).qs

    def get_table(self, request, instance):
        return self.table(self.get_table_data(request, instance))

    def configure_table(self, request, table, instance):
        table.configure(request)

    def get_extra_context(self, request, instance):
        table = self.get_table(request, instance)
        self.configure_table(request, table, instance)
        return {"table": table, "search_value": request.GET.get("q", "")}


class FilterViewWithForm(FilterView):
    filterform_class: type[Form]
    exclude_form_fields: tuple[str, ...] = ()

    def get_filterform_exclude(self):
        return self.exclude_form_fields

    def get_filterform_initial(self):
        if not hasattr(self.filterset.form, "cleaned_data"):
            initial = {}
        else:
            initial = {
                k: v for k, v in self.filterset.form.cleaned_data.items() if k in self.filterform_class.base_fields
            }
        return initial

    def get_filterform(self):
        initial = self.get_filterform_initial()
        exclude = {"exclude": exclude_fields} if (exclude_fields := self.get_filterform_exclude()) else {}
        form = self.filterform_class(initial=initial, **exclude)
        return form

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return super().get_context_data(**kwargs) | {"filterset_form": self.get_filterform()}


class TestResultBaseView(ObjectPermissionRequiredMixin, SingleTableMixin, FilterViewWithForm):
    template_name = "validity/compliance_results.html"
    tab = ViewTab("Test Results", badge=lambda obj: obj.results.count())
    model = models.ComplianceTestResult
    filterset_class = filtersets.ComplianceTestResultFilterSet
    filterform_class = partialcls(forms.TestResultFilterForm, add_m2m_placeholder=True)
    table_class = tables.ComplianceResultTable
    permission_required = "validity.view_compliancetestresult"
    queryset = models.ComplianceTestResult.objects.select_related("test", "device")

    parent_model: type[Model]
    result_relation: str
    read_only: bool = False
    exclude_form_fields: tuple[str, ...] = ()

    def get_table(self, **kwargs):
        table_class = self.get_table_class()
        table = table_class(data=self.get_table_data(), **kwargs)
        table.configure(request=self.request)
        table.exclude = (self.result_relation,)
        return table

    def get_table_kwargs(self):
        return {"user": self.request.user}

    def get_queryset(self):
        return self.queryset.filter(**{self.result_relation: self.kwargs["pk"]})

    def get_object(self):
        return get_object_or_404(self.parent_model, pk=self.kwargs["pk"])

    def get_filterform_exclude(self):
        return super().get_filterform_exclude() + (self.result_relation + "_id",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context | {
            "object": self.get_object(),
            "tab": self.tab,
            "read_only": self.read_only,
            "result_relation": self.result_relation,
        }


class LauncherMixin:
    redirect_viewname = "plugins:validity:script_result"

    # this param must be injected into __init__
    launcher: scripts.Launcher

    def get_success_url(self, job_id: int) -> str:
        return reverse(self.redirect_viewname, kwargs={"pk": job_id})

    def launch_or_render_error(self, params: scripts.ScriptParams, **kwargs):
        if not self.launcher.has_workers:
            messages.error(
                self.request,
                __('Unable to run script: no running RQ worker found for the queue "{}"').format(
                    self.launcher.rq_queue.name
                ),
            )
            return self.get(self.request, **kwargs)
        job = self.launcher(params)
        return HttpResponseRedirect(self.get_success_url(job.pk))
