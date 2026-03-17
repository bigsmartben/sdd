import shlex
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _command_frontmatter_shell_scripts() -> list[str]:
    scripts: set[str] = set()
    commands_dir = REPO_ROOT / "templates" / "commands"

    for command_file in commands_dir.glob("*.md"):
        in_frontmatter = False

        for raw_line in command_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.rstrip()
            if line == "---":
                if in_frontmatter:
                    break
                in_frontmatter = True
                continue

            if not in_frontmatter or not line.lstrip().startswith("sh:"):
                continue

            command = line.split(":", 1)[1].strip()
            scripts.add(shlex.split(command)[0])

    return sorted(scripts)


def _git_mode(rel_path: str) -> str:
    result = subprocess.run(
        ["git", "ls-files", "--stage", "--", rel_path],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    tracked_entry = result.stdout.strip()
    assert tracked_entry, f"{rel_path} is not tracked by git"
    return tracked_entry.split()[0]


def test_command_frontmatter_shell_entrypoints_are_tracked_executable():
    script_paths = _command_frontmatter_shell_scripts()

    assert script_paths, "Expected at least one shell entrypoint in command frontmatter"

    for rel_path in script_paths:
        script_path = REPO_ROOT / rel_path

        assert script_path.exists(), f"Missing shell entrypoint: {rel_path}"
        assert script_path.read_text(encoding="utf-8").startswith("#!"), (
            f"{rel_path} must keep a shebang for direct execution"
        )
        assert _git_mode(rel_path) == "100755", (
            f"{rel_path} must be tracked executable because command frontmatter runs it directly"
        )
