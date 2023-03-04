from dcim.models import Device
from django.db.models import BigIntegerField, Case, QuerySet, When, Manager, Subquery, OuterRef
from django.db.models.functions import Cast


from .models import GitRepo


def get_qs(qs: QuerySet | Manager):
    if isinstance(qs, Manager):
        qs = qs.all()
    return qs


def annotate_git_repos(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    qs = get_qs(qs)
    return qs.annotate(
        git_repo=Case(
            When(
                tenant__custom_field_data__has_key='git_repo',
                then=Subquery(GitRepo.objects.filter(pk=Cast(OuterRef("tenant__custom_field_data__git_repo"), BigIntegerField()))).first(),
            ),
            default=GitRepo.objects.filter(default=True).first()
        )
    )


def annotate_serializer(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    qs = get_qs(qs)
    return qs.annotate