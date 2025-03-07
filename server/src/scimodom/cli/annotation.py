import click

from flask import Blueprint

from scimodom.services.annotation import get_annotation_service
from scimodom.utils.specs.enums import AnnotationSource


annotation_cli = Blueprint("annotation", __name__)


@annotation_cli.cli.command(
    "add", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html."
)
@click.argument("taxa_id", type=click.INT)
@click.option(
    "--source",
    required=True,
    type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
    help="Annotation source.",
)
def add_annotation(taxa_id: int, source: str, **kwargs) -> None:
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
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        click.secho("Aborted!", fg="yellow")
        return

    try:
        annotation_source = AnnotationSource(source)
        annotation_service.create_annotation(annotation_source, taxa_id)
        click.secho("   ... done!", fg="green")
    except FileExistsError:
        click.secho(
            "Directory exists, but no annotation... check for data corruption!",
            fg="red",
        )
        raise click.Abort()
    except Exception as exc:
        click.secho(f"Failed to prepare annotation: {exc}", fg="red")
        raise click.Abort()
