from __future__ import annotations

from pathlib import Path

import pytest
import typer

from specify_cli import download_template_from_github


class _FakeResponse:
    def __init__(self, *, status_code: int = 200, json_data=None, text: str = "", headers: dict | None = None):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._json_data


class _FakeStreamResponse:
    def __init__(self, payload: bytes):
        self.status_code = 200
        self.headers = {"content-length": str(len(payload))}
        self._payload = payload
        self.text = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def iter_bytes(self, chunk_size: int = 8192):
        del chunk_size
        yield self._payload


class _FakeClient:
    def __init__(self, latest_release: dict, payload: bytes):
        self.latest_release = latest_release
        self.payload = payload
        self.get_urls: list[str] = []
        self.stream_urls: list[str] = []

    def get(self, url: str, **kwargs):
        del kwargs
        self.get_urls.append(url)
        if url.endswith("/releases/latest"):
            return _FakeResponse(json_data=self.latest_release)
        raise AssertionError(f"Unexpected GET url: {url}")

    def stream(self, method: str, url: str, **kwargs):
        del kwargs
        assert method == "GET"
        self.stream_urls.append(url)
        return _FakeStreamResponse(self.payload)


def _asset(name: str, download_url: str, size: int = 1234) -> dict:
    return {
        "name": name,
        "browser_download_url": download_url,
        "size": size,
    }


def test_download_template_fails_when_latest_release_is_missing_requested_asset(tmp_path: Path):
    latest = {
        "tag_name": "v2.0.13",
        "assets": [_asset("spec-kit-template-roo-sh-v2.0.13.zip", "https://example.com/roo.zip")],
    }
    payload = b"zip-bytes"
    client = _FakeClient(latest_release=latest, payload=payload)

    with pytest.raises(typer.Exit):
        download_template_from_github(
            "codex",
            tmp_path,
            script_type="sh",
            verbose=False,
            show_progress=False,
            client=client,
        )

    assert len(client.get_urls) == 1
    assert client.get_urls[0].endswith("/releases/latest")
    assert not client.stream_urls


def test_download_template_uses_latest_release_asset_when_present(tmp_path: Path):
    latest = {
        "tag_name": "v2.0.13",
        "assets": [_asset("spec-kit-template-roo-sh-v2.0.13.zip", "https://example.com/roo.zip")],
    }
    payload = b"roo-zip"
    client = _FakeClient(latest_release=latest, payload=payload)

    zip_path, metadata = download_template_from_github(
        "roo",
        tmp_path,
        script_type="sh",
        verbose=False,
        show_progress=False,
        client=client,
    )

    assert metadata["release"] == "v2.0.13"
    assert metadata["filename"] == "spec-kit-template-roo-sh-v2.0.13.zip"
    assert zip_path.exists()
    assert len(client.get_urls) == 1
    assert client.get_urls[0].endswith("/releases/latest")
