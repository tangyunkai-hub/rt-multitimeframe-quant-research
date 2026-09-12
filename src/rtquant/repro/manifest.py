from pathlib import Path
import hashlib
import json


class ManifestIntegrityError(RuntimeError):
    """Raised when a reproducibility manifest does not match its declared inputs."""


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _key_for(path, root=None):
    p = Path(path)
    if root is None:
        return p.name
    root_path = Path(root).resolve()
    try:
        return p.resolve().relative_to(root_path).as_posix()
    except ValueError as exc:
        raise ValueError(f"manifest file is outside root: {p}") from exc


def _file_map(files, root=None):
    out = {}
    for p in files:
        key = _key_for(p, root=root)
        if key in out:
            raise ValueError(
                f"duplicate manifest key: {key}; provide root=... to preserve relative paths"
            )
        out[key] = sha256_file(p)
    return out


def _manifest_sha(payload):
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def build_manifest(*, run_id, files, metadata=None, root=None):
    payload = {
        "run_id": run_id,
        "files": _file_map(files, root=root),
        "metadata": metadata or {},
    }
    payload["manifest_sha256"] = _manifest_sha(payload)
    return payload


def verify_manifest(manifest, *, files, root=None):
    declared_hash = manifest.get("manifest_sha256")
    payload = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    if not declared_hash or _manifest_sha(payload) != declared_hash:
        raise ManifestIntegrityError("manifest self-hash mismatch")
    actual_files = _file_map(files, root=root)
    if actual_files != manifest.get("files"):
        raise ManifestIntegrityError("manifest file hashes do not match current bytes")
    return True
