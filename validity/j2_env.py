from django.utils.text import slugify
from jinja2 import BaseLoader, ChainableUndefined
from jinja2 import Environment as Jinja2Environment


def slug(obj, allow_unicode=False):
    return slugify(str(obj), allow_unicode)


class Environment(Jinja2Environment):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("loader", BaseLoader())
        kwargs.setdefault("undefined", ChainableUndefined)
        super().__init__(*args, **kwargs)
        self.filters["slugify"] = slug
