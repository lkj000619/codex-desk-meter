"""Preserve the operator's frozen source separately from candidate inputs."""
from pathlib import Path
import tempfile
import zipfile

from benchmark_support import digest


def preserve(snapshot, directory):
    snapshot, directory = Path(snapshot).resolve(), Path(directory).resolve()
    if directory.is_relative_to(snapshot):
        raise ValueError("operator archive must stay outside its source snapshot")
    path = directory / "operator-baseline.zip"
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(snapshot.rglob("*")):
            if source.is_symlink():
                raise ValueError("operator snapshot must not contain symlinks")
            if source.is_file():
                archive.write(source, source.relative_to(snapshot).as_posix())
    return {path.name: digest(path.read_bytes()),
            "profile.json": digest((directory / "profile.json").read_bytes())}


def verify(manifest, directory):
    from benchmark import input_bundle_hashes
    from evidence_package import safe_path
    directory = Path(directory).resolve()
    evidence = manifest["operator"]["evidence"]
    if "operator-baseline.zip" not in evidence:
        return False  # Historical records do not gain new requirements.
    for name in ("operator-baseline.zip", "profile.json"):
        if name not in evidence or digest((directory / name).read_bytes()) != evidence[name]:
            raise ValueError("operator baseline evidence mismatch: " + name)
    if evidence["profile.json"] != manifest["agent"]["configuration_sha256"]:
        raise ValueError("operator baseline profile identity mismatch")
    with tempfile.TemporaryDirectory(prefix="meter-restored-baseline-") as temp:
        snapshot = Path(temp)
        with zipfile.ZipFile(directory / "operator-baseline.zip") as archive:
            seen = set()
            for entry in archive.infolist():
                target = safe_path(snapshot, entry.filename)
                if entry.is_dir() or entry.filename in seen:
                    raise ValueError("duplicate or non-file operator archive entry")
                seen.add(entry.filename)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(entry))
        actual = input_bundle_hashes(snapshot, directory / "profile.json",
                                    manifest["baseline_ref"], manifest["execution"]["base_commit"])
        for name, value in actual.items():
            if manifest["execution"][name] != value:
                raise ValueError("operator baseline input hash mismatch: " + name)
    return True
