from pathlib import Path

from specify_cli.runtime_common import resolve_target_path


def test_resolve_target_path_feature_relative_path():
    feature_dir = Path("/tmp/repo/specs/20260323-all-age-dictation-0313")

    resolved = resolve_target_path(feature_dir, "test-matrix.md")

    assert resolved == str((feature_dir / "test-matrix.md").resolve())


def test_resolve_target_path_accepts_repo_relative_specs_path_without_duplication():
    feature_dir = Path("/tmp/repo/specs/20260323-all-age-dictation-0313")

    resolved = resolve_target_path(
        feature_dir,
        "specs/20260323-all-age-dictation-0313/test-matrix.md",
    )

    assert resolved == str((Path("/tmp/repo") / "specs/20260323-all-age-dictation-0313/test-matrix.md").resolve())
