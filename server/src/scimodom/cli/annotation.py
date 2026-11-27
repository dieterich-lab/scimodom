"""Provide a CLI for annotation provisioning."""

import click
from flask import Blueprint

from scimodom.cli.helpers import (
    DOCS_URL,
    CliResponseException,
    confirm,
    register_cli_errors,
)
from scimodom.services.annotation import get_annotation_service
from scimodom.utils.specs.enums import AnnotationSource

annotation_cli = Blueprint("annotation", __name__)

EPILOG = f"Consult {DOCS_URL}#assembly-and-annotation"


@annotation_cli.cli.command(
    "add",
    epilog=EPILOG,
)
@register_cli_errors
@click.option(
    "--yes",
    is_flag=True,
    help="Confirm the action without prompting",
)
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument(
    "taxa-id",
    type=click.INT,
    help="Must reference a valid NCBI taxon",
)
@click.option(
    "--source",
    required=True,
    type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
    help="Annotation source",
)
def add_annotation(
    yes: bool,
    traceback: bool,
    taxa_id: int,
    source: str,
    **kwargs,
):
    """Add annotation.

    Set up the annotation that is current in the database, on the
    assembly it references, for TAXA_ID.
    """
    annotation_service = get_annotation_service()

    if source == "gtrnadb":
        raise CliResponseException("Not implemented for source 'gtrnadb'.")

    annotation_source = AnnotationSource(source)
    try:
        annotation = annotation_service.get_current(annotation_source, taxa_id)
    except Exception as exc:
        raise CliResponseException(
            f"No current {source} annotation for taxon '{taxa_id}'. {exc}"
        ) from exc

    assembly = annotation.inst_assembly
    click.secho(
        f"Preparing {source} annotation release {annotation.release} for "
        f"'{assembly.name}' (taxon {taxa_id})...",
        fg="yellow",
    )
    confirm("Continue?", skip=yes)

    try:
        annotation_service.create_current_annotation(
            annotation_source,
            taxa_id,
        )
        click.secho("   ... done.", fg="green")
    except FileExistsError as exc:
        raise CliResponseException(str(exc)) from exc
    except Exception as exc:
        raise CliResponseException(f"Failed to add annotation. {exc}") from exc
