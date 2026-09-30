import os

import pytest

import main


class FakeResponse:
    def __init__(self, content_type, content=b"data"):
        self.headers = {"content-type": content_type} if content_type else {}
        self.content = content

    def raise_for_status(self):
        pass


@pytest.mark.parametrize("content_type, expected", [
    ("image/jpeg", "jpg"),
    ("video/mp4", "mp4"),
    ("text/html", None),
    (None, None),
])
def test_extension_for(content_type, expected):
    assert main.extension_for(content_type) == expected


def test_link_history(tmp_path):
    main.record_downloaded_link("https://media.example/get?__sig=abc&filename=story1.jpg", tmp_path)
    main.record_downloaded_link("https://cdn.example/a.jpg", tmp_path)
    assert main.load_downloaded_links(tmp_path) == {"story1.jpg", "https://cdn.example/a.jpg"}


def test_link_key_ignores_changing_signature():
    first = "https://media.example/get?__sig=abc&__expires=1&filename=story1.jpg"
    second = "https://media.example/get?__sig=xyz&__expires=2&filename=story1.jpg"
    assert main.link_key(first) == main.link_key(second)


def test_filename_does_not_overwrite(tmp_path):
    first = main.build_filename(tmp_path, "user", 1, "jpg")
    open(first, "w").close()
    second = main.build_filename(tmp_path, "user", 1, "jpg")
    assert first != second
    assert second.endswith("_1_2.jpg")


def test_download_stories(tmp_path, monkeypatch):
    responses = {
        "https://cdn.example/1": FakeResponse("image/jpeg"),
        "https://cdn.example/2": FakeResponse("video/mp4"),
        "https://cdn.example/3": FakeResponse(None),
    }
    monkeypatch.setattr(main.requests, "get", lambda url, timeout: responses[url])

    assert main.download_stories(list(responses), "user", tmp_path) == 2
    files = sorted(os.listdir(tmp_path / "Stories"))
    assert [f.rsplit(".", 1)[1] for f in files] == ["jpg", "mp4"]

    # A second run skips stories that are already downloaded
    assert main.download_stories(list(responses)[:2], "user", tmp_path) == 0


def test_username_is_required():
    with pytest.raises(SystemExit):
        main.main([])
