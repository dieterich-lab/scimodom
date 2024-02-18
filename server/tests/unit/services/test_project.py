from datetime import date, datetime, timezone
from itertools import chain
import json
from pathlib import Path
import uuid

import pytest
import shortuuid
from sqlalchemy import select

from scimodom.database.models import Project, ProjectSource, ProjectContact, Selection
from scimodom.services.project import ProjectService, DuplicateProjectError
import scimodom.utils.utils as utils


def _get_project(
    project_template, external_sources_fmt="list", metadata_fmt="list", missing_key=None
):
    """\
    2023-08-25 Project template (JSON format).

    All keys are required.
    "external_sources" can be None (null in yml).
    "external_sources" and "metadata" can be list of dict, or dict.

    Parameters
    ----------
    external_sources_fmt: str or None
        "external_sources" format (list, dict, or None)
    metadata_fmt: str
        "metadata" format (list or dict)
    missing_key: str or None
        missing_key

    Returns
    -------
    dict
        Project template
    """

    project = project_template.copy()

    external_sources = project["external_sources"]
    if external_sources_fmt == "list":
        pass
    elif external_sources_fmt == "dict":
        external_sources = external_sources[0]
    elif external_sources_fmt is None:
        external_sources = None
    else:
        raise ValueError

    metadata = project["metadata"]
    if metadata_fmt == "list":
        pass
    elif metadata_fmt == "dict":
        metadata = metadata[0]
    else:
        raise ValueError
    project["external_sources"] = external_sources
    project["metadata"] = metadata

    if missing_key:
        if missing_key in project.keys():
            del project[missing_key]
        else:
            if not missing_key == "external_sources" and missing_key in list(
                set(chain.from_iterable(utils.to_list(project["external_sources"])))
            ):
                if external_sources_fmt == "list":
                    del project["external_sources"][0][missing_key]
                else:
                    del project["external_sources"][missing_key]
                # what is None???
            elif not missing_key == "metadata" and missing_key in list(
                set(chain.from_iterable(utils.to_list(project["metadata"])))
            ):
                if metadata_fmt == "list":
                    del project["metadata"][0][missing_key]
                else:
                    del project["metadata"][missing_key]
            elif (
                not missing_key == "organism"
                and missing_key
                in utils.to_list(project["metadata"])[0]["organism"].keys()
            ):
                if metadata_fmt == "list":
                    del project["metadata"][0]["organism"][missing_key]
                else:
                    del project["metadata"]["organism"][missing_key]

    return project


# be careful, this will not pick "new" KeyErrors...
# but test_project_create_project will
@pytest.mark.parametrize(
    "external_sources_fmt,metadata_fmt,missing_key",
    [
        # first level keys w/ or w/o external_sources
        ("list", "list", "title"),
        (None, "list", "title"),
        ("list", "list", "summary"),
        ("list", "list", "contact_name"),
        ("list", "list", "contact_institution"),
        ("list", "list", "contact_email"),
        ("list", "list", "date_published"),
        ("list", "list", "external_sources"),
        ("list", "list", "metadata"),
        # second level keys w/ list or dict
        ("list", "list", "doi"),
        ("dict", "list", "doi"),
        # (None, "list", "doi"), does not raise KeyError!
        ("list", "list", "pmid"),
        ("list", "list", "rna"),
        ("list", "dict", "rna"),
        ("list", "list", "modomics_id"),
        ("list", "list", "tech"),
        ("list", "list", "method_id"),
        ("list", "list", "organism"),
        # third level keys w/ list or dict
        ("list", "list", "taxa_id"),
        ("list", "dict", "taxa_id"),
        ("list", "list", "cto"),
        ("list", "list", "assembly"),
    ],
)
def test_project_validate_keys_error(
    external_sources_fmt,
    metadata_fmt,
    missing_key,
    Session,
    project_template,
    data_path,
):
    project = _get_project(
        project_template,
        external_sources_fmt=external_sources_fmt,
        metadata_fmt=metadata_fmt,
        missing_key=missing_key,
    )
    with pytest.raises(KeyError) as exc:
        ProjectService(Session(), project)._validate_keys()
    assert str(exc.value) == f"'Keys not found: {missing_key}.'"
    assert exc.type == KeyError


def test_project_add_selection(Session, setup, project_template, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)

    project = _get_project(
        project_template,
        external_sources_fmt="list",
        metadata_fmt="list",
        missing_key=None,
    )
    ProjectService(Session(), project)._add_selection()

    expected_records = [(1, 1, 1, 1), (2, 1, 1, 2), (3, 2, 2, 3), (4, 2, 1, 1)]
    with Session() as session, session.begin():
        records = session.execute(select(Selection)).scalars().all()
        records = [
            (r.id, r.modification_id, r.technology_id, r.organism_id) for r in records
        ]
        assert records == expected_records


@pytest.mark.parametrize(
    "external_sources_fmt,metadata_fmt,missing_key",
    [
        ("list", "list", None),
        ("dict", "list", None),
        (None, "list", None),
    ],
)
def test_project_validate_existing_entry(
    external_sources_fmt,
    metadata_fmt,
    missing_key,
    Session,
    setup,
    project_template,
    data_path,
):
    u = uuid.uuid4()
    smid = shortuuid.encode(u)[: ProjectService.SMID_LENGTH]
    stamp = datetime.now(timezone.utc).replace(microsecond=0)

    with Session() as session, session.begin():
        session.add_all(setup)

        contact = ProjectContact(
            contact_name="Contact Name",
            contact_institution="Contact Institution",
            contact_email="Contact Email",
        )
        session.add(contact)
        session.flush()

        project = Project(
            id=smid,
            title="Title",
            summary="Summary",
            contact_id=contact.id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        source1 = ProjectSource(project_id=smid, doi="DOI1", pmid=None)
        source2 = ProjectSource(project_id=smid, doi="DOI2", pmid=22222222)
        session.add_all([project, source1, source2])
        session.commit()

    project = _get_project(
        project_template,
        external_sources_fmt=external_sources_fmt,
        metadata_fmt=metadata_fmt,
        missing_key=missing_key,
    )

    with pytest.raises(DuplicateProjectError) as exc:
        ProjectService(Session(), project)._validate_entry()
    assert (
        str(exc.value)
        == f"At least one similar record exists with SMID = {smid} and title = Title. Aborting transaction!"
    )


def test_project_validate_entry(Session, project_template, data_path):
    project = _get_project(
        project_template,
        external_sources_fmt="list",
        metadata_fmt="list",
        missing_key=None,
    )
    assert ProjectService(Session(), project)._validate_entry() is None


def test_project_create_project(Session, setup, project_template, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)

    stamp = datetime.now(timezone.utc).replace(microsecond=0)  # .isoformat()
    project = _get_project(
        project_template,
        external_sources_fmt="list",
        metadata_fmt="list",
        missing_key=None,
    )
    # AssemblyService tested in test_assembly.py
    project_instance = ProjectService(Session(), project)
    project_instance.create_project(wo_assembly=True)
    project_smid = project_instance.get_smid()

    with Session() as session, session.begin():
        records = session.execute(select(Project)).scalar()
        assert records.title == "Title"
        assert records.summary == "Summary"
        assert records.date_published == datetime.fromisoformat("2024-01-01")
        assert records.date_added.year == stamp.year
        assert records.date_added.month == stamp.month
        assert records.date_added.day == stamp.day
        smid = records.id
        assert smid == project_smid
        contact_id = records.contact_id
        records = session.execute(select(ProjectContact)).scalar()
        assert records.contact_name == "Contact Name"
        assert records.contact_institution == "Contact Institution"
        assert records.contact_email == "Contact Email"
        assert records.id == contact_id
        records = session.execute(select(ProjectSource)).scalars().all()
        sources = [("DOI1", None), ("DOI2", 22222222)]
        for record, source in zip(records, sources):
            assert record.project_id == smid
            assert record.doi == source[0]
            assert record.pmid == source[1]

    project_template = json.load(open(Path(data_path.META_PATH, f"{smid}.json")))
    assert project_template == project
