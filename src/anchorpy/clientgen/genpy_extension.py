from typing import Iterator, Optional, Union as TypingUnion
from genpy import (
    Function as FunctionOriginal,
    Generable,
    Suite,
    Class as BrokenClass,
    FromImport,
)


class Class(BrokenClass):
    def generate(self) -> Iterator[str]:
        bases = self.bases
        if not bases:
            bases = ["object"]

        yield "class {}({}):".format(self.name, ", ".join(bases))
        for f in self.attributes:
            yield from ("    " + f_line for f_line in f.generate())


class TypedParam(Generable):
    def __init__(self, name: str, type_: Optional[str]) -> None:
        self.name = name
        self.type = type_

    def generate(self) -> Iterator[str]:
        if self.type is None:
            yield self.name
        else:
            yield f"{self.name}: {self.type}"


class Break(Generable):
    """
    Inherits from :class:`Generable`.
    .. automethod:: __init__
    """

    def generate(self):
        yield "break"


class Union(Generable):
    def __init__(self, members: list[str]) -> None:
        self.members = members

    def generate(self) -> Iterator[str]:
        joined = ",".join(self.members)
        yield f"typing.Union[{joined}]"


class Tuple(Generable):
    def __init__(self, members: list[str]) -> None:
        self.members = members

    def generate(self) -> Iterator[str]:
        joined = ",".join(self.members)
        yield f"({joined})"


class List(Generable):
    def __init__(self, members: list[str]) -> None:
        self.members = members

    def generate(self) -> Iterator[str]:
        joined = ",".join(self.members)
        yield f"[{joined}]"


class StrDictEntry(Generable):
    def __init__(self, key: str, val: TypingUnion[str, "StrDictEntry"]) -> None:
        self.key = key
        self.val = val

    def generate(self) -> Iterator[str]:
        yield f'"{self.key}": {self.val},'


class StrDict(Generable):
    def __init__(self, items: list[StrDictEntry]) -> None:
        self.items = items

    def generate(self) -> Iterator[str]:
        formatted_items = "".join(str(item) for item in self.items)
        yield "{" + formatted_items + "}"


class IntDictEntry(Generable):
    def __init__(self, key: int, val: str) -> None:
        self.key = key
        self.val = val

    def generate(self) -> Iterator[str]:
        yield f"{self.key}: {self.val},"


class IntDict(StrDict):
    def __init__(self, items: list[IntDictEntry]) -> None:
        self.items = items


class Function(FunctionOriginal):
    def __init__(
        self,
        name: str,
        args: list[TypedParam],
        body: Generable,
        return_type: str,
        decorators: tuple[str, ...] = (),
        is_async: bool = False,
    ) -> None:
        super().__init__(name, args, body, decorators)
        self.return_type = return_type
        self.is_async = is_async

    def generate(self) -> Iterator[str]:
        yield from self.decorators
        arg_strings = []
        for arg in self.args:
            annotation = "" if arg.type is None else f": {arg.type}"
            arg_strings.append(f"{arg.name}{annotation}")
        def_base = "async def" if self.is_async else "def"
        yield "{} {}({}) -> {}:".format(
            def_base, self.name, ", ".join(arg_strings), self.return_type
        )
        yield from self.body.generate()


class StaticMethod(Function):
    def __init__(
        self, name: str, args: list[TypedParam], body: Generable, return_type: str
    ) -> None:
        super().__init__(name, args, body, return_type, ("@staticmethod",))


class ClassMethod(Function):
    def __init__(
        self,
        name: str,
        extra_args: list[TypedParam],
        body: Generable,
        return_type: str,
        is_async: bool = False,
    ) -> None:
        args = [TypedParam("cls", None), *extra_args]
        super().__init__(name, args, body, return_type, ("@classmethod",), is_async)


class Method(Function):
    def __init__(
        self, name: str, extra_args: list[TypedParam], body: Generable, return_type: str
    ) -> None:
        args = [TypedParam("self", None), *extra_args]
        super().__init__(name, args, body, return_type)


class InitMethod(Method):
    def __init__(self, extra_args: list[TypedParam], body: Generable) -> None:
        super().__init__("__init__", extra_args, body, "None")


class Dataclass(Class):
    def __init__(self, name, params: list[TypedParam]) -> None:
        super().__init__(name, None, params)

    def generate(self) -> Iterator[str]:
        yield "@dataclass"
        yield from super().generate()


class TypedDict(Class):
    def __init__(self, name, params: list[TypedParam]) -> None:
        super().__init__(name, ["typing.TypedDict"], params)

    def generate(self) -> Iterator[str]:
        yield from super().generate()


class Try(Generable):
    """A ```try-catch`` block. Inherits from :class:`Generable`.
    .. automethod:: __init__
    """

    def __init__(self, try_body, to_catch, except_body):
        if not isinstance(try_body, Suite):
            try_body = Suite(try_body)
        if not isinstance(except_body, Suite):
            except_body = Suite(except_body)
        self.try_body = try_body
        self.to_catch = to_catch
        self.except_body = except_body

    def generate(self):
        yield "try:"
        yield from self.try_body.generate()
        yield f"except {self.to_catch}:"
        yield from self.except_body.generate()


ANNOTATIONS_IMPORT = FromImport("__future__", ["annotations"])
