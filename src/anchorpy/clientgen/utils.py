from typing import List, Iterator
from genpy import Function as FunctionOriginal, Generable


class TypedParam(Generable):
    def __init__(self, name: str, type_: str) -> None:
        self.name = name
        self.type_ = type_

    def generate(self) -> Iterator[str]:
        yield f"{self.name}: {self.type}"


class Function(FunctionOriginal):
    def __init__(
        self, name: str, args: List[TypedParam], body: Generable, return_type: str
    ) -> None:
        super().__init__(name, args, body)
        self.return_type = return_type

    def generate(self) -> Iterator[str]:
        arg_strings = [f"{arg.name}: {arg.type_}" for arg in self.args]
        yield "def {}({}): -> {}".format(
            self.name, ", ".join(arg_strings), self.return_type
        )
        yield from self.body.generate()
