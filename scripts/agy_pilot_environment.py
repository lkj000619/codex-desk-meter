"""Temporarily scope AGY's global configuration around one pilot command.

AGY CLI 1.2.11 reads global settings, instructions and hooks. This tool keeps
the original bytes in a private local backup and restores them after the child
exits. The active lock and backup survive a hard interruption for recovery.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_atomic(path, data):
    temporary = path.with_name(path.name + ".pilot-tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def read_policy(path):
    policy = json.loads(path.read_text(encoding="utf-8"))
    rules = policy.get("allow")
    if policy.get("policy_version") != 1 or not isinstance(rules, list) or not rules:
        raise ValueError("AGY pilot policy needs version 1 and nonempty allow rules")
    if any(not isinstance(x, str) or not x.startswith("command(") or
           x in {"command(*)", "command(regex:.*)"} or
           "unsandboxed(" in x for x in rules):
        raise ValueError("AGY pilot policy has an unsupported or unscoped rule")
    if len(set(rules)) != len(rules):
        raise ValueError("AGY pilot policy has duplicate rules")
    return rules


def paths_for(gemini_root):
    return {
        "settings": gemini_root / "antigravity-cli" / "settings.json",
        "instructions": gemini_root / "GEMINI.md",
        "hooks": gemini_root / "config" / "hooks.json",
    }


def assert_extensions_clear(gemini_root):
    for directory in (gemini_root / "skills", gemini_root / "antigravity-cli" / "skills"):
        if directory.exists() and any(directory.iterdir()):
            raise ValueError(f"custom AGY skills need separate review: {directory}")
    mcp = gemini_root / "config" / "mcp_config.json"
    if mcp.exists() and json.loads(mcp.read_text(encoding="utf-8")).get("mcpServers"):
        raise ValueError("AGY MCP servers need separate review")


def verify_scoped_environment(gemini_root, policy_path):
    """Fail before launch unless the selected AGY scope is actually active."""
    assert_extensions_clear(gemini_root)
    paths = paths_for(gemini_root)
    if paths["instructions"].exists() or paths["hooks"].exists():
        raise ValueError("AGY global instructions or hooks remain active")
    settings_bytes = paths["settings"].read_bytes()
    settings = json.loads(settings_bytes)
    if settings.get("permissions") != {"allow": read_policy(policy_path)}:
        raise ValueError("AGY scoped command allow list is not active")
    if settings.get("allowNonWorkspaceAccess", False) is not False or settings.get("toolPermission", "request-review") != "request-review":
        raise ValueError("AGY scoped access or approval mode is not active")
    return sha(settings_bytes)


def settings_equivalent(current, expected):
    """Accept only sparse removal of documented default settings."""
    defaults = {"allowNonWorkspaceAccess": False, "toolPermission": "request-review"}
    if set(current) - set(expected):
        return False
    return all(current.get(key, defaults.get(key)) == value for key, value in expected.items())


def restore(backup_dir, *, force=False):
    manifest_path = backup_dir / "active.json"
    if not manifest_path.exists():
        raise ValueError("no active AGY pilot backup")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key, entry in manifest["files"].items():
        target = Path(entry["path"])
        expected_active = entry.get("active_sha256")
        if not force and entry.get("active_absent") and target.exists():
            raise ValueError(f"AGY {key} appeared during pilot; inspect before restoring: {target}")
        if not force and expected_active is not None:
            if not target.exists() or (
                sha(target.read_bytes()) != expected_active and
                not settings_equivalent(json.loads(target.read_text(encoding="utf-8")), entry["active_settings"])
            ):
                raise ValueError(f"AGY {key} changed during pilot; inspect before restoring: {target}")
    for key, entry in manifest["files"].items():
        target = Path(entry["path"])
        if entry["existed"]:
            original = (backup_dir / (key + ".original")).read_bytes()
            if sha(original) != entry["original_sha256"]:
                raise ValueError(f"AGY {key} backup hash mismatch")
            write_atomic(target, original)
        elif target.exists():
            target.unlink()
    manifest_path.unlink()
    return manifest


@contextmanager
def scoped_environment(gemini_root, policy_path, backup_dir):
    assert_extensions_clear(gemini_root)
    rules = read_policy(policy_path)
    paths = paths_for(gemini_root)
    if not paths["settings"].is_file():
        raise ValueError("AGY settings.json is missing")
    if (backup_dir / "active.json").exists():
        raise ValueError("an AGY pilot backup is already active; restore it first")
    backup_dir.mkdir(parents=True, exist_ok=True)
    original_settings = json.loads(paths["settings"].read_text(encoding="utf-8"))
    scoped_settings = dict(original_settings)
    scoped_settings["permissions"] = {"allow": rules}
    scoped_settings["allowNonWorkspaceAccess"] = False
    scoped_settings["toolPermission"] = "request-review"
    scoped_bytes = (json.dumps(scoped_settings, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest = {"policy_sha256": sha(policy_path.read_bytes()), "files": {}}
    for key, target in paths.items():
        existed = target.is_file()
        original = target.read_bytes() if existed else b""
        if existed:
            (backup_dir / (key + ".original")).write_bytes(original)
        manifest["files"][key] = {
            "path": str(target), "existed": existed,
            "original_sha256": sha(original) if existed else None,
            "active_sha256": sha(scoped_bytes) if key == "settings" else None,
            "active_settings": scoped_settings if key == "settings" else None,
            "active_absent": key in ("instructions", "hooks"),
        }
    (backup_dir / "active.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        write_atomic(paths["settings"], scoped_bytes)
        for key in ("instructions", "hooks"):
            if paths[key].exists():
                paths[key].unlink()
        yield {"settings_sha256": sha(scoped_bytes), "policy_sha256": manifest["policy_sha256"]}
    finally:
        restore(backup_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "restore"])
    parser.add_argument("--gemini-root", type=Path, default=Path.home() / ".gemini")
    parser.add_argument("--policy", type=Path, default=Path(__file__).resolve().parents[1] /
                        "experiments/config/agy-pilot-permissions.json")
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--force", action="store_true", help="restore after inspecting concurrent edits")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == "restore":
        restore(args.backup_dir, force=args.force)
        print("AGY global files restored")
        return
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("run requires a child command after --")
    workspace = Path(__file__).resolve().parents[1]
    if args.backup_dir.resolve().is_relative_to(workspace):
        parser.error("backup-dir must be outside the repository")
    if os.name == "nt":
        probe = subprocess.run(["powershell", "-NoProfile", "-Command",
                                "@(Get-Process agy -ErrorAction SilentlyContinue).Count"],
                               capture_output=True, text=True)
        if probe.returncode != 0 or probe.stdout.strip() != "0":
            raise ValueError("close other AGY processes before the scoped pilot")
    with scoped_environment(args.gemini_root, args.policy, args.backup_dir) as identity:
        print(json.dumps(identity), flush=True)
        child_env = os.environ.copy()
        child_env["AGY_CLI_DISABLE_AUTO_UPDATE"] = "true"
        code = subprocess.call(command, env=child_env)
    print("AGY global files restored", flush=True)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
