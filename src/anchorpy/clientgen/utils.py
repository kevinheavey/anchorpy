from typing import List, Iterator
from genpy import Function as FunctionOriginal, Generable, Suite, Class


class TypedParam(Generable):
    def __init__(self, name: str, type_: str) -> None:
        self.name = name
        self.type = type_

    def generate(self) -> Iterator[str]:
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
        yield f"Union[{joined}]"


class Function(FunctionOriginal):
    def __init__(
        self, name: str, args: List[TypedParam], body: Generable, return_type: str
    ) -> None:
        super().__init__(name, args, body)
        self.return_type = return_type

    def generate(self) -> Iterator[str]:
        arg_strings = [f"{arg.name}: {arg.type}" for arg in self.args]
        yield "def {}({}): -> {}".format(
            self.name, ", ".join(arg_strings), self.return_type
        )
        yield from self.body.generate()


class Dataclass(Class):
    def __init__(self, name, params: list[TypedParam]) -> None:
        super().__init__(name, None, params)

    def generate(self) -> Iterator[str]:
        yield "@dataclass"
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

        for line in self.try_body.generate():
            yield line

        yield f"except {self.to_catch}:"
        for line in self.except_body.generate():
            yield line
