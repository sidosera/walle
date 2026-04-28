from tester import Eval, Filter, Gt, ListScan, Literal, Project, Select, TestCase


def case(**kwa) -> TestCase:
    t = int(kwa["threshold"])
    return TestCase(
        Project(
            child=Filter(
                child=ListScan(
                    [
                        {"name": "a", "value": 3},
                        {"name": "b", "value": 7},
                        {"name": "c", "value": 12},
                    ],
                ),
                predicate=Gt(Select("value"), Literal(t)),
            ),
            expressions=(
                Eval("name", Select("name")),
                Eval("value", Select("value")),
            ),
        ),
    )
