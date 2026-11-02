from scimodom.services.web import WebService


class _Response:
    ok = True

    def __init__(self):
        self.closed = False

    def json(self):
        return {"a": 1}

    def iter_content(self, chunk_size):
        yield b"data"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_request_as_json_has_timeout(mocker):
    get = mocker.patch("scimodom.services.web.requests.get", return_value=_Response())
    assert WebService.request_as_json("http://x") == {"a": 1}
    assert get.call_args.kwargs["timeout"] == WebService.TIMEOUT


def test_stream_request_has_timeout(mocker):
    from io import BytesIO

    get = mocker.patch("scimodom.services.web.requests.get", return_value=_Response())
    out = BytesIO()
    WebService.stream_request_to_file("http://x", out)
    assert out.getvalue() == b"data"
    assert get.call_args.kwargs["timeout"] == WebService.TIMEOUT
