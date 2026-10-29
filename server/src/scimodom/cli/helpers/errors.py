"""Provide exception and error constructors."""

import click


class CliResponseException(Exception):
    """For expected command failures."""


class _CliException(click.ClickException):
    def format_message(self) -> str:
        return click.style(self.message, fg="red")


def register_cli_errors(func):
    """Format expected errors unless traceback is requested."""

    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        try:
            return ctx.invoke(func, *args, **kwargs)
        except CliResponseException as exc:
            if ctx.params.get("traceback", False):
                raise
            raise _CliException(str(exc)) from None

    return click.decorators.update_wrapper(wrapper, func)
