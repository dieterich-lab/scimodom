"""Provide a CLI for annotation provisioning."""

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
    "add",
    epilog="Consult https://dieterich-lab.github.io/scimodom/flask.html#assembly-and-annotation",
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument("taxa_id", type=click.INT, help="Must reference a valid NCBI taxon")
@click.option(
    "--source",
    required=True,
    type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
    help="Annotation source",
)
def add_annotation(yes: bool, traceback: bool, taxa_id: int, source: str, **kwargs):
    """Add annotations.

    Set up the annotation that is current in the database, on the
    assembly it references. The annotation must exist in the database,
    and so must the assembly, which is set up by 'flask assembly add'.

    This is not a way to install an arbitrary release: the release
    comes from the annotation record, and upgrading to another one
    replaces the current annotation.
    """
    annotation_service = get_annotation_service()

    if source == "gtrnadb":
        raise CliResponseException("Not implemented for source 'gtrnadb'.")

    annotation_source = AnnotationSource(source)
    try:
        annotation = annotation_service.get_annotation(annotation_source, taxa_id)
    except Exception as exc:
        raise CliResponseException(
            f"No current {source} annotation for organism '{taxa_id}'. {exc}"
        ) from exc

    assembly = annotation.inst_assembly
    click.secho(
        f"Preparing {source} annotation release {annotation.release} for "
        f"'{assembly.name}' (organism {taxa_id})...",
        fg="yellow",
    )
    confirm("Continue?", skip=yes)

    try:
        annotation_service.create_annotation(annotation_source, taxa_id)
        click.secho("   ... done.", fg="green")
    except FileExistsError as exc:
        raise CliResponseException(
            "Directory exists, but no annotation... check for data corruption!",
        ) from exc
    # no need to handle generic exception... but first check what
    # create annotation raises..
    except Exception as exc:
        raise CliResponseException(f"Failed to prepare annotation. {exc}") from exc
