from .inspector import func_frame, func_local_ann
from .exceptions import MutationError

from rich.console import Console
from rich.syntax import Syntax

class Fail:
    def __init__(
        self,
        origin,
        affects
    ) -> None:
        self.origin = origin
        self.affects = affects

    def construct_syntax(
        self
    ):
        console = Console()
        with open("robotmicha", "rt") as code_file:
            syntax = Syntax(code_file.read(), "python", padding= 1)
        console.print(syntax)

    def __str__(self) -> str:
        return f"Failure from {self.origin} affecting test {self.affects}"

class Test:
    def __init__(
        self,
        testName: str,
        func,
        args: list[any],
        expect: any
    ) -> None:
        self.name = testName
        self.func = func
        self.args = args
        self.expect = expect

        #logger.debug(f"**{testName}** -> {func.__name__}({', '.join([str(_) for _ in args])})")
        _res = self.run_test()

        if type(_res) == Fail:
            #logger.error("Failed test")
            #logger.info(_res)
            pass
    
    def run_test(
        self
    ):
        frame, result = func_frame(
            self.func,
            *self.args
        )

        takes_types = self.func.__annotations__
        inner_types = func_local_ann(self.func)

        args = list(self.args)
        need = list(takes_types.items())[:-1]

        for i, arg in enumerate(args):
            needed =  need[i]
            if str(type(arg)) != str(needed[1]) and str(
                    needed[1]) != str(any):
                raise Exception(
                    f'Invalid type passed to {self.func.__name__}{list(takes_types.items())}\nExpected: {needed[0]} of {needed[1]}\nGot: {arg} of {type(arg)}'
                )

        for arg in list(frame.f_locals.items()):
            if arg[0] in inner_types and type(arg[1]).__name__ != str(
                    inner_types[arg[0]]) and str(any.__name__) != str(
                        inner_types[arg[0]]):
                raise MutationError(
                    f'Final value of the variable [{arg[0]}] has mutated.\n{arg[0]} :: {inner_types[arg[0]]} --> {type(arg[1]).__name__}\nMutation of inner types is dissallowed in type-asserted function ({self.func.__name__})'
                )
        if type(result) != list(takes_types.items())[-1]:
            return Fail(frame, self)

        return result