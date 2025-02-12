import sys
from typing import Final

from clipstick import _help
from clipstick._exceptions import ClipStickError
from clipstick._parse import tokenize, validate_model
from clipstick._tokens import Command, TPydanticModel

DUMMY_ENTRY_POINT: Final[str] = "my-cli-app"


def parse(
    model: type[TPydanticModel],
    args: list[str] | None = None,
    entry_point: str | None = None,
) -> TPydanticModel:
    """Create an instance of the provided model.

    Leave `args` to None in production. Only use it for testing.

    Args:
        model: The pydantic class we want to populate.
        args: The list of arguments. This is useful for testing.
            Provide a list and check if your model is parsed correctly.
            If not provided clipstick will evaluate the arguments from `sys.argv`.
        entry_point: Entry point name. This is useful for testing.
            Provide an entry point name and check for value in help output.
            If not provided clipstick will evaluate an entry point from `sys.argv`.

    Returns:
        An instance of the pydantic class we provided as argument populated with the provided args.
    """
    try:
        validate_model(model)
    except ClipStickError as err:
        _help.error(err)
        sys.exit(1)
    if args is None:
        entry_point, args = sys.argv[0], sys.argv[1:]
    elif entry_point is None:
        # Normally the first item in your sys.argv is the command/entrypoint you've entered.
        # During testing you don't provide that (only the actual arguments you enter after that).
        entry_point = DUMMY_ENTRY_POINT

    root_node = Command(field=entry_point, cls=model, parent=None)
    try:
        tokenize(model=model, sub_command=root_node)
    except ClipStickError as err:
        _help.error(err)
        sys.exit(1)
    try:
        success, idx = root_node.match(0, args)
    except ClipStickError as err:
        _help.error(err)
        sys.exit(1)
    if not idx == len(args) or not success:
        _help.error("Unable to consume all provided arguments.")
        _help.suggest_help()
        sys.exit(1)

    try:
        parsed = root_node.parse()
    except ClipStickError as err:
        _help.error(err)
        sys.exit(1)

    return parsed
