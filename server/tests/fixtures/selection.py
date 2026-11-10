import pytest

from scimodom.database.models import (
    Organism,
    Modification,
    DetectionTechnology,
    ProjectSelection,
    Selection,
)


@pytest.fixture
def selection(Session, setup):  # noqa
    session = Session()
    modification1 = Modification(rna="WTS", modomics_id="2000000006A")
    modification2 = Modification(rna="WTS", modomics_id="2000000005C")
    technology1 = DetectionTechnology(tech="Technology 1", method_id="91b145ea")
    technology2 = DetectionTechnology(tech="Technology 2", method_id="0ee048bc")
    organism1 = Organism(cto="Cell type 1", taxa_id=9606)
    organism2 = Organism(cto="Cell type 2", taxa_id=9606)
    session.add_all(
        [modification1, modification2, organism1, organism2, technology1, technology2]
    )
    session.flush()
    # selection == (1, 1, 1), (2, 1, 1), (1, 2, 2), (1, 1, 2), (2, 2, 2)
    selection1 = Selection(
        modification_id=modification1.id,
        organism_id=organism1.id,
        technology_id=technology1.id,
    )
    selection2 = Selection(
        modification_id=modification2.id,
        organism_id=organism1.id,
        technology_id=technology1.id,
    )
    selection3 = Selection(
        modification_id=modification1.id,
        organism_id=organism2.id,
        technology_id=technology2.id,
    )
    selection4 = Selection(
        modification_id=modification1.id,
        organism_id=organism1.id,
        technology_id=technology2.id,
    )
    selection5 = Selection(
        modification_id=modification2.id,
        organism_id=organism2.id,
        technology_id=technology2.id,
    )

    session.add_all([selection1, selection2, selection3, selection4, selection5])
    session.commit()


@pytest.fixture
def project_selection(Session, project, selection):  # noqa
    """Selections of project '12345678'.

    Same as the selection fixture (the second project has no selection).
    """
    session = Session()
    # (modification, organism, technology)
    combinations = [(1, 1, 1), (2, 1, 1), (1, 2, 2), (1, 1, 2), (2, 2, 2)]
    session.add_all(
        [
            ProjectSelection(
                project_id="12345678",
                modification_id=modification_id,
                organism_id=organism_id,
                technology_id=technology_id,
            )
            for modification_id, organism_id, technology_id in combinations
        ]
    )
    session.commit()
