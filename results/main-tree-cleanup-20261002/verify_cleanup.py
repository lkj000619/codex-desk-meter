"""Verify the chosen documentation cleanup without changing historical evidence."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASELINE = json.loads((OUT / "preservation-baseline.json").read_text(encoding="utf-8"))
MOVES = {
    "docs/experiments/e2e-contract-implementation-plan.md":
        "docs/archive/plans/2026-09-13-e2e-contract-implementation-plan.md",
    "docs/experiments/host-device-pipeline-implementation-plan.md":
        "docs/archive/plans/2026-09-13-host-device-pipeline-implementation-plan.md",
}
LOGS = [name for name in BASELINE["source_metadata"] if name.endswith(".log")]
NOTE = re.compile(
    br"\r?\n<!-- archive-note:2026-10-02:start -->\r?\n.*?"
    br"<!-- archive-note:2026-10-02:end -->\r?\n", re.DOTALL,
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    problems = []
    preserved = []
    for name, expected in BASELINE["protected_hashes"].items():
        data = (ROOT / name).read_bytes()
        if name == "docs/archive/experiments/readiness-review-20260913.md":
            data, count = NOTE.subn(b"", data)
            if count != 1:
                problems.append({"kind": "archive_note_count", "file": name, "count": count})
        if digest(data) != expected:
            problems.append({"kind": "protected_bytes_changed", "file": name})
        else:
            preserved.append(name)

    relocations = []
    for old, new in MOVES.items():
        data, count = NOTE.subn(b"", (ROOT / new).read_bytes())
        valid = count == 1 and digest(data) == BASELINE["source_metadata"][old]["sha256"] and not (ROOT / old).exists()
        relocations.append({"old": old, "new": new, "original_bytes_preserved": valid, "sha256": digest(data)})
        if not valid:
            problems.append({"kind": "relocation_or_original_body", "file": new})

    logs = []
    for name in LOGS:
        data = (ROOT / name).read_bytes()
        blob = git("show", ":" + name)
        expected = BASELINE["source_metadata"][name]["sha256"]
        ignored = subprocess.run(["git", "check-ignore", "--no-index", "-q", name], cwd=ROOT).returncode
        tracked = name in git("ls-files", "-z", "--", name).decode().split("\0")
        attributes = git("check-attr", "text", "diff", "merge", "--", name).decode().splitlines()
        valid = digest(data) == digest(blob) == expected and ignored == 1 and tracked and all(line.endswith(": unset") for line in attributes)
        logs.append({"file": name, "worktree_sha256": digest(data), "git_blob_sha256": digest(blob), "valid": valid, "attributes": attributes})
        if not valid:
            problems.append({"kind": "registered_log_bytes", "file": name})
    ordinary_log_ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "results/main-tree-cleanup-20261002/unreviewed.log"], cwd=ROOT,
    ).returncode == 0
    staged = sorted(git("diff", "--cached", "--name-only").decode().splitlines())
    if staged != sorted(set(BASELINE["staged_before"]) | set(LOGS)):
        problems.append({"kind": "unexpected_staged_paths", "paths": staged})
    if not ordinary_log_ignored:
        problems.append({"kind": "ordinary_log_ignore_removed"})

    names = set(git("ls-files", "-z").decode().split("\0"))
    names.update(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
    markdown = sorted(name for name in names if name.endswith(".md") and (ROOT / name).is_file())
    links, broken, ignored_links = [], [], []
    for name in markdown:
        text = (ROOT / name).read_text(encoding="utf-8-sig")
        for match in re.finditer(r"\[[^\]]*\]\((<[^>]+>|[^)]+)\)", text):
            target = match.group(1).strip().strip("<>")
            if not target or target.startswith(("http:", "https:", "mailto:", "app:", "#")):
                continue
            path = Path(unquote(target.split("#", 1)[0]))
            if not path.is_absolute():
                path = (ROOT / name).parent / path
            path = path.resolve()
            item = {"file": name, "line": text.count("\n", 0, match.start()) + 1, "target": target}
            links.append(item)
            if not path.exists():
                broken.append(item)
            elif path.is_relative_to(ROOT) and subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", path.relative_to(ROOT).as_posix()], cwd=ROOT,
            ).returncode == 0:
                ignored_links.append(item)
    if broken or ignored_links:
        problems.append({"kind": "markdown_links", "broken": broken, "ignored": ignored_links})

    trailing = []
    for name in sorted(names):
        path = ROOT / name
        if path.is_file() and path.suffix in {".md", ".py", ".json"}:
            for index, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if line.rstrip(" \t") != line:
                    trailing.append({"file": name, "line": index})
    if trailing:
        problems.append({"kind": "trailing_whitespace", "findings": trailing})

    whitespace = {}
    for label, args in (("worktree", ("diff", "--check")), ("index", ("diff", "--cached", "--check"))):
        run = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
        whitespace[label] = {"exit": run.returncode, "output": run.stdout.decode("utf-8", errors="replace")}
        if run.returncode:
            problems.append({"kind": "diff_check", "scope": label})
    head = git("rev-parse", "HEAD").decode().strip()
    if head != BASELINE["head"]:
        problems.append({"kind": "head_changed"})

    result = {"checked_on": "2026-10-02", "branch": git("branch", "--show-current").decode().strip(), "head": head,
              "choices": {"plans": "docs/archive/plans/", "logs": "register_only_three_reviewed_logs"},
              "protected_files_verified": len(preserved), "protected_failures": len(BASELINE["protected_hashes"]) - len(preserved),
              "relocations": relocations, "logs": logs, "staged_paths": staged, "ordinary_logs_still_ignored": ordinary_log_ignored,
              "markdown_files": len(markdown), "local_links_checked": len(links), "broken_links": broken,
              "links_to_ignored_files": ignored_links, "trailing_whitespace": trailing, "diff_checks": whitespace, "problems": problems,
              "scope": "Local file links, byte preservation, Git index and ignore/attributes. Excludes external URL/heading-anchor checks and new runtime/hardware tests."}
    (OUT / "evidence.json").write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("protected_files_verified", "protected_failures", "markdown_files", "local_links_checked", "problems")}, ensure_ascii=True))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
