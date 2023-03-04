import jq as pyjq


__all__ = ["jq"]


def jq(expression, json):
    return pyjq.all(expression, json)
