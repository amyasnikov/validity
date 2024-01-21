from contextlib import nullcontext
from unittest.mock import Mock

import pytest
from factories import CommandFactory, DataFileFactory, SerializerDBFactory, state_item

from validity.compliance.exceptions import NoComponentError, SerializationError
from validity.compliance.serialization import Serializable
from validity.compliance.state import State, StateItem


class TestStateItem:
    @pytest.mark.parametrize(
        "command_kwargs, contains_config, name, verbose_name",
        [
            (None, True, "config", "Config"),
            ({"retrieves_config": True}, True, "config", "Config"),
            ({"retrieves_config": False, "name": "Cmd1", "label": "cmd1"}, False, "cmd1", "Cmd1"),
        ],
    )
    @pytest.mark.django_db
    def test_contains_config(self, command_kwargs, contains_config, name, verbose_name):
        command = CommandFactory(**command_kwargs) if command_kwargs is not None else None
        serializer = SerializerDBFactory()
        data_file = DataFileFactory()
        item = StateItem(serializer, data_file, command)
        assert item.contains_config == contains_config
        assert item.name == name
        assert item.verbose_name == verbose_name

    @pytest.mark.parametrize(
        "has_datafile, has_serializer, expected_error, serialized",
        [
            (True, True, None, {"some": ["serialized", "data"]}),
            (False, True, NoComponentError, None),
            (True, False, NoComponentError, None),
            (False, False, NoComponentError, None),
        ],
    )
    def test_serialized(self, has_datafile, has_serializer, expected_error, serialized):
        serializer = Mock(**{"serialize.return_value": serialized}) if has_serializer else None
        data_file = Mock() if has_datafile else None
        item = StateItem(serializer, data_file, None)
        ctx = pytest.raises(expected_error) if expected_error is not None else nullcontext()
        if expected_error is not None:
            assert isinstance(item.error, expected_error)
        with ctx:
            assert item.serialized == serialized
        if has_serializer and has_datafile:
            serializer.serialize.assert_called_once_with(data_file.data_as_string)


class TestState:
    @pytest.mark.django_db
    def test_get_item(self):
        item1 = state_item("item1", {"k1": "v1"})
        item2 = state_item("item2", {"k2": "v2"}, command=CommandFactory(retrieves_config=True))
        item_err = state_item("item_err", {}, data_file=None)
        del item_err.__dict__["serialized"]
        state = State({"item1": item1, "config": item2, "item_err": item_err}, config_command_label="item2")
        assert state["item1"] == state.item1 == {"k1": "v1"}
        assert state["item2"] == state.item2 == state.config == state["config"] == {"k2": "v2"}
        assert state.get_full_item("item1") == item1
        assert state.get("item3") is None
        assert state.get("item_err", ignore_errors=True) is None
        with pytest.raises(SerializationError):
            state.get("item_err")

    @pytest.mark.django_db
    def test_from_commands(self):
        s1 = SerializerDBFactory()
        s2 = SerializerDBFactory()
        f1 = DataFileFactory()
        f2 = DataFileFactory()
        cmd1 = CommandFactory(serializer=s1)
        cmd2 = CommandFactory(serializer=s2)
        cmd1.data_file = f1
        cmd2.data_file = f2
        cmd2.retrieves_config = True
        state = State.from_commands([cmd1, cmd2])
        assert state.keys() == {cmd1.label, "config"}
        assert state.config_command_label == cmd2.label
        assert state.get_full_item(cmd1.label) == StateItem(s1, f1, cmd1)
        assert state.get_full_item("config") == StateItem(s2, f2, cmd2)

    @pytest.mark.django_db
    def test_with_config(self):
        items = [state_item("item1", {}), state_item("item2", {})]
        cfg_item = Serializable(SerializerDBFactory(), DataFileFactory())
        state = State({i.name: i for i in items}).with_config(cfg_item)
        assert state.get_full_item("config").serializer == cfg_item.serializer
        assert state.get_full_item("config").data_file == cfg_item.data_file
        assert state.get_full_item("config").command is None
        cfg_item2 = StateItem(SerializerDBFactory(), DataFileFactory(), None)
        assert state.with_config(cfg_item2).get_full_item("config") == cfg_item2
