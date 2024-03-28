from http import HTTPStatus

import pytest
from django.db.models import Model
from django.urls import reverse
from factory.django import DjangoModelFactory


class ApiBaseTest:
    api_url = "/api/plugins/validity/{}/"
    entity: str

    def _test_get(self, client, pk=None):
        resp = client.get(self.url(pk))
        assert resp.status_code == HTTPStatus.OK, resp.data
        if pk:
            self.get_extra_checks(resp.json(), pk)

    def get_extra_checks(self, resp_json, pk):
        pass

    @classmethod
    def url(cls, id_=None):
        api_url = cls.api_url.format(cls.entity)
        if id_:
            api_url += f"{id_}/"
        return api_url


class PostMixin:
    post_body: dict[str, str | int | type[DjangoModelFactory] | list[type[DjangoModelFactory]]]

    @classmethod
    def resolve_post_body(cls):
        #  making data_file point to the same data_source
        if "data_source" in cls.post_body and "data_file" in cls.post_body:
            data_source = cls.post_body["data_source"]()
            cls.post_body["data_source"] = data_source.pk
            cls.post_body["data_file"] = cls.post_body["data_file"](source=data_source).pk
        for k, v in cls.post_body.items():
            if isinstance(v, type):
                cls.post_body[k] = v().pk
            elif v and isinstance(v, list) and isinstance(v[0], type):
                cls.post_body[k] = [item().pk for item in v]


class ApiGetTest(ApiBaseTest):
    factory: type[DjangoModelFactory]

    @pytest.mark.django_db
    def test_get(self, admin_client):
        obj_id = self.factory().pk
        self._test_get(admin_client)
        self._test_get(admin_client, obj_id)


class ApiPostGetTest(PostMixin, ApiBaseTest):
    def _test_post(self, client):
        self.resolve_post_body()
        resp = client.post(self.url(), self.post_body, content_type="application/json")
        assert resp.status_code == HTTPStatus.CREATED, resp.content
        return resp.json()["id"]

    @pytest.mark.django_db
    def test_post_get(self, admin_client):
        obj_id = self._test_post(admin_client)
        self._test_get(admin_client)
        self._test_get(admin_client, obj_id)


class ViewTest(PostMixin):
    model_class: type[Model]
    factory_class: type[DjangoModelFactory]
    detail_suffixes = {"", "edit", "delete"}
    get_suffixes: list[str] = ["", "list", "add", "edit", "delete", "bulk_delete"]
    post_suffixes: list[str] = ["edit", "delete", "add", "bulk_delete"]

    @classmethod
    def create_models(cls):
        return cls.factory_class().pk

    def view_urls(self, suffixes, obj_id):
        for suffix in suffixes:
            view_name = self.model_class._meta.model_name
            if suffix:
                view_name += f"_{suffix}"
            url_kwargs = {"pk": obj_id} if suffix in self.detail_suffixes else {}
            yield view_name, reverse(f"plugins:validity:{view_name}", kwargs=url_kwargs)

    def post_view_urls(self, obj_id):
        yield from self.view_urls(self.post_suffixes, obj_id)

    def get_view_urls(self, obj_id):
        yield from self.view_urls(self.get_suffixes, obj_id)

    @pytest.mark.django_db
    def test_post(self, admin_client, subtests):
        self.resolve_post_body()
        obj_id = self.create_models()
        for view_name, url in self.post_view_urls(obj_id):
            body = self.post_body if not view_name.endswith("delete") else {"confirm": "True"}
            with subtests.test(id=view_name):
                resp = admin_client.post(url, body)
                assert resp.status_code == HTTPStatus.FOUND, url

    @pytest.mark.django_db
    def test_get(self, admin_client, subtests):
        obj_id = self.create_models()
        for view_name, url in self.get_view_urls(obj_id):
            with subtests.test(id=view_name):
                resp = admin_client.get(url)
                assert resp.status_code in {HTTPStatus.OK, HTTPStatus.FOUND}, url
