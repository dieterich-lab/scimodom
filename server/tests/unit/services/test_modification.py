from scimodom.services.modification import ModificationService


class MockAnnotationService:
    def __init__(self):
        pass


def _get_modification_service(Session):
    return ModificationService(
        session=Session(), annotation_service=MockAnnotationService()
    )


def test_get_modification_site(Session, dataset):  # noqa
    modification_service = _get_modification_service(Session)
    response = modification_service.get_modification_site(
        "17", 100001, 100002, 0, 10, []
    )
    assert len(response["records"]) == 2
    assert response["records"][0]["dataset_id"] == "d1"
    assert response["records"][1]["dataset_id"] == "d2"
    assert response["records"][0]["cto"] == "Cell type 1"
    assert response["records"][1]["cto"] == "Cell type 2"
    assert response["records"][0]["tech"] == "Technology 1"
    assert response["records"][1]["tech"] == "Technology 2"
    assert response["records"][0]["score"] == 1000
    assert response["records"][1]["score"] == 10
