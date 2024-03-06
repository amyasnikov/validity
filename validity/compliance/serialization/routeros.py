import io
import logging
import re
from dataclasses import dataclass, field
from typing import Generator, Literal

from validity.utils.misc import reraise
from ..exceptions import SerializationError


logger = logging.getLogger(__name__)


class LineParsingError(SerializationError):
    pass


def non_quoted_characters(line: str) -> Generator[tuple[int, str], None, None]:
    """
    Generator returns pairs (char_position, char) for each char in line not placed inside the quotes
    Quoted substring will be returned as 1 single character with char_position equal to first character
    """

    quote_open = False
    quote_start = -1
    for i, char in enumerate(line):
        if char == '"' and (not i or line[i - 1] != "\\"):
            quote_open = not quote_open
            if quote_open:
                quote_start = i
            else:
                yield i, line[quote_start : i + 1]
            continue
        if quote_open:
            continue
        yield i, char


@dataclass
class ParsedLine:
    method: Literal["add", "set"]
    find_by: tuple[str, str] | tuple[()] = ()
    properties: dict[str, str] = field(default_factory=dict)
    implicit_name: bool = False

    @classmethod
    def _extract_find(cls, line: str) -> tuple[tuple[str, str | int | bool], str]:
        find, line = line.split("]", maxsplit=1)
        find = find[1:].replace("find", "", 1).strip()
        find_key, find_value = find.split("=", maxsplit=1)
        find_value = cls._transform_value(find_key, find_value)
        return (find_key, find_value), line

    @staticmethod
    def _replace_line_breaks(line: str) -> str:
        drop_match = re.compile(r"\\\n +")
        new_line = []
        backslash_seq = []
        for _, char in non_quoted_characters(line):
            if char == "\\" or char in {"\n", " "} and backslash_seq:
                backslash_seq.append(char)
                continue
            if not drop_match.fullmatch("".join(backslash_seq)):
                new_line.extend(backslash_seq)
            backslash_seq = []
            new_line.append(char)
        return "".join(new_line)

    @staticmethod
    def _transform_value(key: str, value: str) -> str | int | bool:
        if value and len(value) > 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        if key in {"name", "comment"}:
            return value
        if value.isdigit():
            return int(value)
        booleans = {"yes": True, "no": False}
        if value in booleans:
            return booleans[value]
        return value

    @classmethod
    def from_plain_text(cls, line: str) -> "ParsedLine":
        method, line = line.split(maxsplit=1)
        if method not in {"add", "set"}:
            raise LineParsingError("Unknown line")
        find = ()
        if line.startswith("["):
            find, line = cls._extract_find(line)
        properties = {}
        sub_start = 0
        implicit_name = False
        line = cls._replace_line_breaks(line).strip()
        for char_num, char in non_quoted_characters(line + " "):
            if char == " ":
                kvline = line[sub_start:char_num].strip(" \n")
                if kvline and "=" not in kvline:
                    kvline = "name=" + kvline
                    implicit_name = True
                with reraise(ValueError, LineParsingError, f'"{kvline}" cannot be split into key/value'):
                    key, value = kvline.split("=", maxsplit=1)
                properties[key] = cls._transform_value(key, value)
                sub_start = char_num + 1
        return cls(method=method, find_by=find, properties=properties, implicit_name=implicit_name)


def parse_config(plain_config: str) -> dict:
    result = {}
    context_path = []
    prevlines = []
    cfgfile = io.StringIO(plain_config)
    for line_num, line in enumerate(cfgfile, start=1):
        if line.startswith(("#", ":")) or line == "\n":
            continue
        if line.startswith("/"):
            context_path = line[1:-1].split()
            continue
        if line.endswith("\\\n"):
            prevlines.append(line)
            continue
        if prevlines:
            line = "".join(prevlines) + line
            prevlines = []
        try:
            parsed_line = ParsedLine.from_plain_text(line)
        except LineParsingError as e:
            e.args = (e.args[0] + f", config line {line_num}",) + e.args[1:]
            raise
        current_context = result
        for key in context_path:
            try:
                current_context = current_context[key]
            except KeyError:
                current_context[key] = {}
                current_context = current_context[key]
        if parsed_line.find_by or parsed_line.method == "add" or parsed_line.implicit_name:
            if "values" not in current_context:
                current_context["values"] = []
            current_context["values"].append(parsed_line.properties)
            if parsed_line.find_by:
                current_context["values"][-1]["find_by"] = [
                    {"key": parsed_line.find_by[0], "value": parsed_line.find_by[1]}
                ]
        else:
            current_context["properties"] = parsed_line.properties
    return result


def serialize_ros(plain_data: str, template: str, parameters: dict):
    return parse_config(plain_data)
