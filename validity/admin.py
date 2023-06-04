from django.contrib import admin

from validity import models


@admin.register(models.ComplianceReport)
class ReportAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ComplianceTestResult)
class ResultAdmin(admin.ModelAdmin):
    pass
