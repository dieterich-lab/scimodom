import click

from scimodom.services.annotation import AnnotationSource, get_annotation_service


def add_annotation(taxa_id: int, source: AnnotationSource, **kwargs) -> None:
    """Provide a CLI function to manage annotation.

    Annotation must exists (only latest version allowed).

    :param taxa_id: Taxonomy ID.
    :type taxa_id: int
    :param source: Annotation source
    :type source: AnnotationSource
    """
    annotation_service = get_annotation_service()
    click.secho(
        f"Preparing {source.value} annotation for {taxa_id}. If this annotation already exists, nothing will be done...",
        fg="green",
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    try:
        annotation_service.create_annotation(source, taxa_id, **kwargs)
    except FileExistsError:
        click.secho(
            "Directory exists, but no annotation... check for data corruption. Aborting!",
            fg="red",
        )
        return
    except Exception as exc:
        click.secho(f"Failed to prepare annotation: {exc}. Aborting!", fg="red")
        return
    click.secho("... done!", fg="green")
