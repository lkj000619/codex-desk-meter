"""Read-only project tree audit; output stays in this dated report directory."""
import ast
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PREFIX = OUT.relative_to(ROOT).as_posix() + "/"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, encoding="utf-8", stderr=subprocess.DEVNULL).strip()


def normalized(value):
    return re.sub(r"\s+", " ", value).strip()


def active(name):
    return (name == "README.md" or name == "AGENTS.md" or name.startswith("docs/")) and not any(
        part in name for part in ("/archive/", "/evidence/", "/plans/", "/overview/"))


def audit():
    head_files = set(git("ls-tree", "-r", "--name-only", "HEAD").splitlines())
    tracked = set(git("ls-files").splitlines())
    new = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    files = sorted(name for name in tracked | new if not name.startswith(PREFIX) and (ROOT / name).is_file())
    new = {name for name in new if not name.startswith(PREFIX)}
    bytes_by_hash, texts, duplicates = defaultdict(list), {}, []
    counts = Counter(name.split("/", 1)[0] if "/" in name else "(root files)" for name in files)
    nested = Counter("/".join(name.split("/")[:2]) for name in files if "/" in name)
    for name in files:
        path = ROOT / name
        if path.stat().st_size <= 8 * 1024 * 1024:
            data = path.read_bytes()
            bytes_by_hash[hashlib.sha256(data).hexdigest()].append(name)
        if path.suffix in {".md", ".py", ".ps1", ".json", ".yaml", ".html", ".txt"}:
            try:
                texts[name] = path.read_text(encoding="utf-8-sig")
            except UnicodeError:
                pass
    duplicates = [{"sha256": key, "files": names} for key, names in bytes_by_hash.items() if len(names) > 1]
    normalized_json = defaultdict(list)
    for name, value in texts.items():
        if name.endswith(".json"):
            try:
                key = hashlib.sha256(json.dumps(json.loads(value), sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()
                normalized_json[key].append(name)
            except ValueError:
                pass
    semantic_json = [{"sha256": key, "files": names} for key, names in normalized_json.items() if len(names) > 1]
    paragraphs, lines, grams = defaultdict(list), defaultdict(list), {}
    for name, value in texts.items():
        if not name.endswith(".md") or not active(name):
            continue
        for match in re.finditer(r"(?:[^\n]|\n(?!\s*\n))+", value):
            block = normalized(match.group(0))
            if len(block) >= 100 and not block.startswith(("#", "```", "|", ">")):
                paragraphs[block].append({"file": name, "line": value.count("\n", 0, match.start())+1})
        for index, line in enumerate(value.splitlines(), 1):
            cleaned = normalized(line.strip(" *-"))
            if len(cleaned) >= 70 and not cleaned.startswith(("|", "#", "```")):
                lines[cleaned].append({"file": name, "line": index})
        words = re.findall(r"[\w가-힣]+", value.lower())
        grams[name] = {tuple(words[index:index+5]) for index in range(max(0, len(words)-4))}
    repeated_paragraphs = [{"text": key, "locations": locations} for key, locations in paragraphs.items()
                           if len({item["file"] for item in locations}) > 1]
    repeated_lines = [{"text": key, "locations": locations} for key, locations in lines.items()
                      if len({item["file"] for item in locations}) > 1]
    overlaps = []
    for left, right in itertools.combinations(grams, 2):
        common = len(grams[left] & grams[right])
        denominator = min(len(grams[left]), len(grams[right]))
        if common >= 25 and denominator and common / denominator >= 0.12:
            overlaps.append({"left": left, "right": right, "shared_5grams": common, "shorter_document_overlap": round(common/denominator, 3)})
    links = []
    for name, value in texts.items():
        if not name.endswith(".md"):
            continue
        for match in re.finditer(r"\[[^\]]*\]\((<[^>]+>|[^)]+)\)", value):
            target = match.group(1).strip().strip("<>")
            if not target or target.startswith(("http:", "https:", "mailto:", "app:", "#")):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            path = Path(target)
            if not path.is_absolute():
                path = (ROOT / name).parent / path
            path = path.resolve()
            local = path.is_relative_to(ROOT)
            relative = path.relative_to(ROOT).as_posix() if local else None
            ignored = bool(git("check-ignore", "--no-index", relative)) if local and relative not in tracked and _ignored(relative) else False
            links.append({"file": name, "line": value.count("\n", 0, match.start())+1, "target": target,
                          "exists": path.exists(), "repository_path": relative, "in_head": relative in head_files,
                          "tracked": relative in tracked, "ignored": ignored, "external_local_path": not local})
    function_clones = defaultdict(list)
    for name, value in texts.items():
        if not name.startswith("scripts/") or "/tests/" in name or not name.endswith(".py"):
            continue
        module = ast.parse(value, filename=name)
        for node in module.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.end_lineno-node.lineno < 8:
                continue
            key = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
            function_clones[key].append({"file": name, "function": node.name, "line": node.lineno, "lines": node.end_lineno-node.lineno+1})
    case_groups = defaultdict(list)
    for name in files:
        case_groups[name.casefold()].append(name)
    result = {"reviewed_on": "2026-10-02", "branch": git("branch", "--show-current"), "head": git("rev-parse", "HEAD"),
              "scope": "Tracked plus nonignored untracked project files; excludes this report; hashes files <=8 MiB. Local ignored skill/cache/artifact directories are separately inventoried, not repository duplicates.",
              "head_file_count": len(head_files), "working_file_count": len(files), "untracked_project_files": len(new),
              "changed_tracked_paths": git("diff", "--name-only").splitlines(), "missing_tracked_files": sorted(tracked-set(files)),
              "counts_by_root": dict(sorted(counts.items())), "counts_by_directory": dict(sorted(nested.items())),
              "byte_duplicate_groups": duplicates, "semantic_json_duplicate_groups": semantic_json,
              "active_repeated_paragraphs": repeated_paragraphs, "active_repeated_lines": repeated_lines,
              "active_text_overlap_candidates": sorted(overlaps, key=lambda item: -item["shorter_document_overlap"]),
              "function_body_duplicates": [values for values in function_clones.values() if len(values)>1],
              "case_collisions": [values for values in case_groups.values() if len(values)>1],
              "markdown_files": sum(name.endswith(".md") for name in files), "local_links_checked": len(links),
              "broken_working_links": [item for item in links if not item["exists"]],
              "links_to_ignored_files": [item for item in links if item["ignored"]],
              "links_to_untracked_files": [item for item in links if item["repository_path"] and not item["tracked"] and not item["ignored"]],
              "external_local_links": [item for item in links if item["external_local_path"]],
              "working_links_missing_in_head": [item for item in links if item["repository_path"] and item["exists"] and not item["in_head"]],
              "files": files}
    (OUT / "evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for key in ("head_file_count", "working_file_count", "untracked_project_files", "counts_by_root", "markdown_files", "local_links_checked"):
        print(key, result[key])
    for key in ("byte_duplicate_groups", "semantic_json_duplicate_groups", "active_repeated_paragraphs", "active_repeated_lines",
                "function_body_duplicates", "case_collisions", "broken_working_links", "links_to_ignored_files", "links_to_untracked_files", "external_local_links"):
        print(key, len(result[key]))


def _ignored(relative):
    return subprocess.run(["git", "check-ignore", "--no-index", relative], cwd=ROOT, stdout=subprocess.DEVNULL).returncode == 0


if __name__ == "__main__":
    audit()
