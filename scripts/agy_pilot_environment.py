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
import signal
import subprocess
import sys
import uuid


_OWNED_SCOPES = {}
_OWNER_ENV = "AGY_PILOT_LOCK_TOKEN"


class ChildCleanupError(RuntimeError):
    """Child termination is unconfirmed; keep the scoped files for recovery."""


def run_child(command, env):
    process = subprocess.Popen(command, env=env, start_new_session=os.name != "nt",
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
    try:
        return process.wait()
    except BaseException:
        try:
            if os.name == "nt":
                stopped = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                         capture_output=True, timeout=30)
                if stopped.returncode != 0:
                    raise ChildCleanupError("AGY child tree termination is unconfirmed; stop its processes before manual restore")
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=30)
        except BaseException as error:
            raise ChildCleanupError("AGY child tree termination is unconfirmed; stop its processes before manual restore") from error
        raise


@contextmanager
def root_lock(gemini_root):
    """Hold one OS lock across setup, execution and restoration.

    Keep the lock file permanently: unlinking it could let two processes lock
    different file objects at the same path. The separate owner journal survives
    process termination and requires explicit recovery before another run.
    """
    lock_path = gemini_root / ".agy-pilot.lock"
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise ValueError("AGY global root lock is active") from error
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise ValueError("AGY global root lock is active") from error
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def owner_path(gemini_root):
    return gemini_root / ".agy-pilot-owner.json"


def assert_owner(gemini_root, backup_dir, manifest, *, allow_missing=False):
    ownership = manifest.get("lock")
    if not ownership or ownership.get("gemini_root") != str(gemini_root) or ownership.get("backup_dir") != str(backup_dir):
        raise ValueError("AGY lock owner does not match this backup")
    journal = owner_path(gemini_root)
    if allow_missing and not journal.exists():
        return ownership
    if not journal.is_file() or json.loads(journal.read_text(encoding="utf-8")) != ownership:
        raise ValueError("AGY lock owner journal does not match the backup")
    return ownership


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
    declared_reads = {
        "read_file(C:/Espressif/v5.3.2/esp-idf)",
        "read_file(C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source)",
    }
    if any(not isinstance(x, str) or (not x.startswith("command(") and x not in declared_reads) or
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


def effective_rules(policy_path, workspace=None):
    rules = read_policy(policy_path)
    if workspace is not None:
        workspace = Path(workspace).resolve()
        if workspace == Path(workspace.anchor) or workspace == Path.home().resolve():
            raise ValueError("workspace scope must be a dedicated project directory")
        rules = rules + ["write_file(" + workspace.as_posix() + ")"]
    return rules


def verify_scoped_environment(gemini_root, policy_path, workspace=None):
    """Fail before launch unless the selected AGY scope is actually active."""
    gemini_root = Path(gemini_root).resolve()
    journal = owner_path(gemini_root)
    if not journal.is_file():
        raise ValueError("AGY scope has no active lock owner")
    ownership = json.loads(journal.read_text(encoding="utf-8"))
    token = _OWNED_SCOPES.get(gemini_root, os.environ.get(_OWNER_ENV))
    if not token or token != ownership.get("token"):
        raise ValueError("AGY scope lock belongs to another owner")
    if gemini_root not in _OWNED_SCOPES:
        try:
            with root_lock(gemini_root):
                pass
        except ValueError:
            pass  # The parent still holds the exclusive lock.
        else:
            raise ValueError("AGY scope lock owner is no longer active; restore first")
    backup_dir = Path(ownership["backup_dir"])
    manifest = json.loads((backup_dir / "active.json").read_text(encoding="utf-8"))
    assert_owner(gemini_root, backup_dir, manifest)
    assert_extensions_clear(gemini_root)
    paths = paths_for(gemini_root)
    if paths["instructions"].exists() or paths["hooks"].exists():
        raise ValueError("AGY global instructions or hooks remain active")
    settings_bytes = paths["settings"].read_bytes()
    settings = json.loads(settings_bytes)
    if settings.get("permissions") != {"allow": effective_rules(policy_path, workspace)}:
        raise ValueError("AGY scoped command allow list is not active")
    if settings.get("allowNonWorkspaceAccess", False) is not False or settings.get("toolPermission", "request-review") != "request-review":
        raise ValueError("AGY scoped access or approval mode is not active")
    assert_owner(gemini_root, backup_dir, manifest)
    return sha(settings_bytes)


def settings_equivalent(current, expected):
    """Accept only sparse removal of documented default settings."""
    defaults = {"allowNonWorkspaceAccess": False, "toolPermission": "request-review"}
    if set(current) - set(expected):
        return False
    return all(current.get(key, defaults.get(key)) == value for key, value in expected.items())


def restore(backup_dir, *, force=False):
    backup_dir = Path(backup_dir).resolve()
    manifest_path = backup_dir / "active.json"
    if not manifest_path.exists():
        raise ValueError("no active AGY pilot backup")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    gemini_root = Path(manifest["files"]["settings"]["path"]).resolve().parent.parent
    with root_lock(gemini_root):
        # Re-read after acquisition so concurrent recovery cannot use stale data.
        if not manifest_path.exists():
            raise ValueError("no active AGY pilot backup")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not manifest.get("lock") and owner_path(gemini_root).exists():
            raise ValueError("AGY lock owner prevents legacy backup restoration")
        return restore_owned(gemini_root, backup_dir, manifest, force=force)


def restore_owned(gemini_root, backup_dir, manifest, *, force=False):
    """Restore while the caller holds the root lock; validate before any write."""
    finish_only = bool(manifest.get("lock")) and not owner_path(gemini_root).exists()
    if manifest.get("lock"):
        assert_owner(gemini_root, backup_dir, manifest, allow_missing=finish_only)
    expected_paths = paths_for(gemini_root)
    if set(manifest["files"]) != set(expected_paths) or any(
        Path(entry["path"]).resolve() != expected_paths[key]
        for key, entry in manifest["files"].items()
    ):
        raise ValueError("AGY backup targets do not match the locked global root")
    originals = {}
    for key, entry in manifest["files"].items():
        target = Path(entry["path"])
        if entry["existed"]:
            original = (backup_dir / (key + ".original")).read_bytes()
            if sha(original) != entry["original_sha256"]:
                raise ValueError(f"AGY {key} backup hash mismatch")
            originals[key] = original
        # A crash can leave a mixture of original and scoped files during
        # setup or restoration. Exact original bytes are always safe to keep.
        if (entry["existed"] and target.is_file() and target.read_bytes() == originals[key]) or (
            not entry["existed"] and not target.exists()
        ):
            continue
        if finish_only:
            raise ValueError("AGY lock owner is missing and global files are not restored")
        expected_active = entry.get("active_sha256")
        if not force and entry.get("active_absent") and target.exists():
            raise ValueError(f"AGY {key} appeared during pilot; inspect before restoring: {target}")
        if not force and expected_active is not None:
            if not target.exists() or (
                sha(target.read_bytes()) != expected_active and
                not settings_equivalent(json.loads(target.read_text(encoding="utf-8")), entry["active_settings"])
            ):
                raise ValueError(f"AGY {key} changed during pilot; inspect before restoring: {target}")
    for key, entry in (() if finish_only else manifest["files"].items()):
        target = Path(entry["path"])
        if entry["existed"]:
            write_atomic(target, originals[key])
        elif target.exists():
            target.unlink()
    if manifest.get("lock") and not finish_only:
        owner_path(gemini_root).unlink()
    (backup_dir / "active.json").unlink()
    return manifest


@contextmanager
def scoped_environment(gemini_root, policy_path, backup_dir, workspace=None):
    gemini_root = Path(gemini_root).resolve()
    backup_dir = Path(backup_dir).resolve()
    with root_lock(gemini_root):
        if owner_path(gemini_root).exists():
            raise ValueError("an AGY global scope is active; restore its backup first")
        with prepare_scoped_environment(gemini_root, policy_path, backup_dir, workspace) as identity:
            yield identity


@contextmanager
def prepare_scoped_environment(gemini_root, policy_path, backup_dir, workspace):
    assert_extensions_clear(gemini_root)
    rules = effective_rules(policy_path, workspace)
    if workspace is not None and not Path(workspace).is_dir():
        raise ValueError("workspace scope directory does not exist")
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
    ownership = {"token": uuid.uuid4().hex, "gemini_root": str(gemini_root),
                 "backup_dir": str(backup_dir), "pid": os.getpid()}
    manifest = {"policy_sha256": sha(policy_path.read_bytes()), "files": {}, "lock": ownership}
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
    write_atomic(backup_dir / "active.json", (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    try:
        write_atomic(owner_path(gemini_root), (json.dumps(ownership) + "\n").encode("utf-8"))
    except BaseException:
        # Publication may have completed before the write reported failure.
        # Keep ownership/backup paired even at this interruption boundary.
        restore_owned(gemini_root, backup_dir, manifest)
        raise
    _OWNED_SCOPES[gemini_root] = ownership["token"]
    prepared = False
    restore_on_exit = True
    try:
        write_atomic(paths["settings"], scoped_bytes)
        for key in ("instructions", "hooks"):
            if paths[key].exists():
                paths[key].unlink()
        prepared = True
        yield {"settings_sha256": sha(scoped_bytes), "policy_sha256": manifest["policy_sha256"],
               "lock_token": ownership["token"]}
    except ChildCleanupError:
        restore_on_exit = False
        raise
    finally:
        try:
            if restore_on_exit:
                restore_owned(gemini_root, backup_dir, manifest, force=not prepared)
        finally:
            _OWNED_SCOPES.pop(gemini_root, None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "restore"])
    parser.add_argument("--gemini-root", type=Path, default=Path.home() / ".gemini")
    parser.add_argument("--policy", type=Path, default=Path(__file__).resolve().parents[1] /
                        "experiments/config/agy-pilot-permissions.json")
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--workspace", type=Path,
                        help="grant writes only to this checkout; runner checks it against manifest")
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
    with scoped_environment(args.gemini_root, args.policy, args.backup_dir, workspace=args.workspace) as identity:
        print(json.dumps(identity), flush=True)
        child_env = os.environ.copy()
        child_env["AGY_CLI_DISABLE_AUTO_UPDATE"] = "true"
        child_env[_OWNER_ENV] = identity["lock_token"]
        code = run_child(command, child_env)
    print("AGY global files restored", flush=True)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
