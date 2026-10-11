"""Arithmp: Command-line interface for the Arithmp package."""

from pathlib import Path
from typing import TextIO, cast

import click

from .parser import Parser, ParserException


@click.command()
@click.argument("expression", required=False)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="Start an interactive prompt.",
)
@click.option(
    "-f",
    "--file",
    "input_file",
    type=click.File("r", encoding="utf-8"),
    help="Parse the given file.",
)
def main(
    expression: str | None,
    interactive: bool,
    input_file: TextIO | None,
) -> None:
    """
    Main entry point for the Arithmp command-line interface.
    """
    if (interactive or input_file is not None) and expression is not None:
        raise click.UsageError(
            "EXPRESSION cannot be used with --file or --interactive."
        )
    if expression is None and not interactive and input_file is None:
        raise click.UsageError("Missing argument 'EXPRESSION'.")

    parser = Parser()

    if expression is not None:
        try:
            if (result := parser.parse(expression)) is not None:
                click.echo(result)
        except ParserException as e:
            click.echo(f"Error: {e}")
            return

    if input_file is not None:
        try:
            result = parser.parse(input_file.read())

            if result is not None and not interactive:
                click.echo(result)
        except ParserException as e:
            click.echo(f"Error: {e}")
            return

    if interactive:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.history import FileHistory

        session = PromptSession(
            history=FileHistory(Path.home().joinpath(".arithmp_history")),
            completer=WordCompleter(
                lambda: list(parser.functions.keys()) + list(parser.variables.keys())
            ),
        )

        while True:
            expression = cast(str, session.prompt("> ")).strip()
            if not expression:
                continue
            try:
                result = parser.parse(expression)
                if result is not None:
                    click.echo(result)
            except SystemExit:
                break
            except ParserException as e:
                click.echo(f"Error: {e}")


if __name__ == "__main__":
    main()
