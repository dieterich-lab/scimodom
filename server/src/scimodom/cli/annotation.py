import click

from flask import Blueprint

from scimodom.services.annotation import get_annotation_service
from scimodom.utils.specs.enums import AnnotationSource

from scimodom.cli.helpers import (
    CliResponseException,
    register_cli_errors,
    confirm,
)

annotation_cli = Blueprint("annotation", __name__)


@annotation_cli.cli.command(
    "add", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html."
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument("taxa_id", type=click.INT)
@click.option(
    "--source",
    required=True,
    type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
    help="Annotation source.",
)
def add_annotation(
    yes: bool, traceback: bool, taxa_id: int, source: str, **kwargs
) -> None:
    """Add annotations.

    Annotation must exists in the database (only latest version allowed).

    \b
    TAXA_ID is the organism taxonomic ID.
    """
    annotation_service = get_annotation_service()

    if source == "gtrnadb":
        click.secho("Not Implemented...", fg="red")
        raise click.Abort()

    click.secho(f"Preparing {source} annotation for {taxa_id}...", fg="green")
    confirm("Continue?", skip=yes)

    try:
        annotation_source = AnnotationSource(source)
        annotation_service.create_annotation(annotation_source, taxa_id)
        click.secho("   ... done!", fg="green")
    except FileExistsError as exc:
        raise CliResponseException(
            "Directory exists, but no annotation... check for data corruption!",
        ) from exc
    # no need to handle generic exception... but first check what
    # create annotation raises..
    except Exception as exc:
        raise CliResponseException(f"Failed to prepare annotation: {exc}") from exc
