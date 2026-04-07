from pathlib import Path

from src.webui.server import app, resolve_static_bundle


def test_resolve_static_bundle_accepts_valid_bundle(tmp_path: Path):
    static_dir = tmp_path / "static"
    assets_dir = static_dir / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "index-test.js").write_text("console.log('ok')", encoding="utf-8")
    (assets_dir / "index-test.css").write_text("body{}", encoding="utf-8")
    (static_dir / "index.html").write_text(
        '<script type="module" src="/assets/index-test.js"></script>'
        '<link rel="stylesheet" href="/assets/index-test.css">',
        encoding="utf-8",
    )

    assert resolve_static_bundle(tmp_path) == static_dir


def test_resolve_static_bundle_rejects_missing_assets(tmp_path: Path):
    static_dir = tmp_path / "static"
    static_dir.mkdir(parents=True)
    (static_dir / "index.html").write_text(
        '<script type="module" src="/assets/index-missing.js"></script>',
        encoding="utf-8",
    )

    assert resolve_static_bundle(tmp_path) is None


def test_root_route_is_registered():
    assert any(
        getattr(route, "name", None) == "static" and getattr(route, "path", None) in {"", "/"}
        for route in app.routes
    )
