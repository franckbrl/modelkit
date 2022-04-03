import inspect
from pydantic import BaseModel
from rich.markup import escape
from rich.tree import Tree
import typing
from typing import Dict, List, Optional, Tuple, Union
from textwrap import indent


def pretty_print_type(typ):
    def print_list(my_list, car_from, car_to, max_car_in_line=50):
        inline_s = car_from + ",".join(my_list) + car_to
        if len(inline_s) <= max_car_in_line:
            return escape(inline_s)
        multiline_s = car_from + "\n"
        multiline_s += indent(",\n".join(my_list), " " * 2)
        multiline_s += "\n" + car_to
        return escape(multiline_s)

    # For simple types
    if type(typ) is type:
        return escape(typ.__name__)

    # For lists
    if type(typ) is list:
        return print_list([pretty_print_type(x) for x in typ], "[", "]")

    # For tuples
    if type(typ) is tuple:
        return print_list([pretty_print_type(x) for x in typ], "(", ")")

    # For dicts
    if type(typ) is dict:
        return print_list(
            [f"{key}: " + pretty_print_type(item) for key, item in typ.items()],
            "{",
            "}",
        )

    # For typing types
    if type(typ) is typing._GenericAlias:
        s = escape(typ._name)
        if typ.__args__:
            a = [pretty_print_type(x) for x in typ.__args__]
            if s:
                s += print_list(a, "[", "]")
            else:
                s = print_list(a, "(", ")")
        return s

    # For pydantic classes
    if inspect.isclass(typ) and issubclass(typ, BaseModel):
        return escape(typ.schema_json(indent=2, by_alias=True))

    typ_str = str(typ)
    if "'" in typ_str:  # for class wrapper
        typ_str = typ_str.split("'")[1]
    return escape(typ_str)


def describe(obj, t=None):
    if not t:
        t = Tree("")

    if hasattr(obj, "__fields__"):
        for field_name, field in obj.__fields__.items():
            sub_t = t.add(
                f"[deep_sky_blue1]{field_name}[/deep_sky_blue1] [dim]: "
                f"{pretty_print_type(field.outer_type_)}[/dim]"
            )
            describe(getattr(obj, field_name), t=sub_t)
    elif isinstance(obj, dict):
        if obj:
            for field_name, field in obj.items():
                sub_t = t.add(
                    f"[deep_sky_blue1]{escape(field_name)}[/deep_sky_blue1] [dim]: "
                    f"{pretty_print_type(type(field).__name__)}[/dim]"
                )
                describe(field, t=sub_t)
        else:
            t.label += " = [orange3]{}[/orange3]"
    elif isinstance(obj, type):
        t.label += f" = [orange3]{escape(str(obj.__name__))}[/orange3] type"
    elif isinstance(obj, (str, int, float, bool)):
        t.label += f" = [orange3]{escape(repr(obj))}[/orange3]"
    elif obj is None:
        t.label += " = [orange3]None[/orange3]"
    elif isinstance(obj, object):
        t.label += (
            f" = [orange3]{escape(str(obj.__class__.__name__))}[/orange3] " "instance"
        )
        try:
            obj.describe(t=t)
        except AttributeError:
            try:
                for var in vars(obj):
                    if var.startswith("_"):
                        continue
                    sub_t = t.add(
                        f"[deep_sky_blue1]{var}[/deep_sky_blue1] [dim]: "
                        f"{pretty_print_type(type(getattr(obj, var)).__name__)}"
                        f"[/dim] = {escape(repr(getattr(obj, var)))}"
                    )
            except TypeError:
                t.label += f" = [orange3]{escape(str(obj))}[/orange3]"
    return t
