from functools import wraps

from validity.utils.json import jq


def postprocess_jq(func):
    @wraps(func)
    def inner(plain_data: str, template: str, parameters: dict):
        result = func(plain_data, template, parameters)
        if jq_expression := parameters.get("jq_expression"):
            result = jq.first(jq_expression, result)
        return result

    return inner
