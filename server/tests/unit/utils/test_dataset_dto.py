from scimodom.utils.dtos.dataset import DatasetPostRequest


EXAMPLE_BODY = """
{
    "smid": "abcdef12",
    "file_id": "id",
    "rna_type": "WTS",
    "modification_id": [1, 2],
    "organism_id": 1,
    "assembly_id": 2,
    "technology_id": 3,
    "title": "Title"
}
"""


def test_dataset_post_request():
    template = DatasetPostRequest.model_validate_json(EXAMPLE_BODY)
    assert template.modification_id == [1, 2]
    assert template.title == "Title"
