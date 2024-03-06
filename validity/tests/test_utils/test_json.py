import pytest

from validity.utils.json import jq, transform_json


class TestTransformJson:
    JSON = {
        "users": [{"name": "John", "age": 30}, {"name": "Jack", "age": 20}],
        "groups": {
            "admin": {
                "members": ["John", "Anna", "Jack"],
            },
        },
    }

    def test_change_value(self):
        result = transform_json(
            self.JSON,
            match_fn=lambda key, val: isinstance(val, dict) and "name" in val,
            transform_fn=lambda key, val: (key, val | {"nickname": val["name"] + str(val["age"])}),
        )
        assert result["users"][0]["nickname"] == "John30"
        assert result["users"][1]["nickname"] == "Jack20"
        assert result["groups"] == self.JSON["groups"]

    def test_delete(self):
        result = transform_json(self.JSON, match_fn=lambda key, val: val == "Anna", transform_fn=lambda key, val: None)
        assert result["groups"]["admin"]["members"] == ["John", "Jack"]

    def test_change_key(self):
        result = transform_json(
            self.JSON, match_fn=lambda key, val: key == "admin", transform_fn=lambda key, val: ("admin2", val)
        )
        assert result["groups"]["admin2"] == self.JSON["groups"]["admin"]
        assert "admin" not in result["groups"]


@pytest.mark.parametrize(
    "data, expression, result",
    [
        ({"a": {"b": "one", "c": "two"}}, ". | mkarr(.a.b)", {"a": {"b": ["one"], "c": "two"}}),
        ({"a": {"b": ["one"], "c": "two"}}, ". | mkarr(.a.b)", {"a": {"b": ["one"], "c": "two"}}),
        ({"a": "10.2", "b": {"c": "20"}}, ". | mknum(.b)", {"a": "10.2", "b": {"c": 20}}),
        ({"a": "10.2", "b": {"c": "20"}}, ". | mknum", {"a": 10.2, "b": {"c": 20}}),
    ],
)
def test_jq(data, expression, result):
    assert jq.first(expression, data) == result
