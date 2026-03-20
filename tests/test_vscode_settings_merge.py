import json
from pathlib import Path

from specify_cli import merge_json_files


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_merge_json_files_sanitizes_cmd_style_chcp_args_for_powershell_profiles(tmp_path: Path) -> None:
    existing = {
        "terminal.integrated.profiles.windows": {
            "PowerShell": {
                "path": "C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "args": ["/k", "chcp 65001 >nul"],
            },
            "Command Prompt": {
                "path": "C:\\WINDOWS\\System32\\cmd.exe",
                "args": ["/k", "chcp 65001 >nul"],
            },
        }
    }
    new_content = {
        "chat.tools.terminal.autoApprove": {
            ".specify/scripts/powershell/": True,
        }
    }

    existing_path = tmp_path / "settings.json"
    _write_json(existing_path, existing)

    merged = merge_json_files(existing_path, new_content)

    assert merged["terminal.integrated.profiles.windows"]["PowerShell"]["args"] == [
        "-NoExit",
        "-Command",
        "chcp 65001 > $null",
    ]
    assert merged["terminal.integrated.profiles.windows"]["Command Prompt"]["args"] == [
        "/k",
        "chcp 65001 >nul",
    ]
    assert merged["chat.tools.terminal.autoApprove"][".specify/scripts/powershell/"] is True


def test_merge_json_files_sanitizes_shell_args_windows_when_default_profile_is_powershell(tmp_path: Path) -> None:
    existing = {
        "terminal.integrated.defaultProfile.windows": "PowerShell",
        "terminal.integrated.shellArgs.windows": ["/k", "chcp 65001 >nul"],
    }
    existing_path = tmp_path / "settings.json"
    _write_json(existing_path, existing)

    merged = merge_json_files(existing_path, {})

    assert merged["terminal.integrated.shellArgs.windows"] == [
        "-NoExit",
        "-Command",
        "chcp 65001 > $null",
    ]


def test_merge_json_files_keeps_valid_powershell_args_unchanged(tmp_path: Path) -> None:
    existing = {
        "terminal.integrated.profiles.windows": {
            "PowerShell": {
                "path": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
                "args": ["-NoExit", "-Command", "chcp 65001 > $null"],
            }
        }
    }
    existing_path = tmp_path / "settings.json"
    _write_json(existing_path, existing)

    merged = merge_json_files(existing_path, {})

    assert merged["terminal.integrated.profiles.windows"]["PowerShell"]["args"] == [
        "-NoExit",
        "-Command",
        "chcp 65001 > $null",
    ]
