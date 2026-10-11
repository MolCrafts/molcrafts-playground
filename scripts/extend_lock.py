#!/usr/bin/env python3
"""Add MolCrafts wheels to the Pyodide 314 lock.

``pyodide-lock`` 0.2 calls ``uv`` with ``--python-platform=wasm32-pyodide2024``.
uv 0.13 has no ``wasm32-pyodide2026`` value, so it refuses the molrs wheel
tagged ``pyemscripten_2026_0_wasm32``. Pyodide 314.0.6 itself is abi 2026_0
(Emscripten 5.0.3). This script copies that lock, points existing entries at
the jsDelivr CDN, and appends the browser wheels shipped with the site.

``loadPyodideOptions.lockFileURL`` is resolved against the JupyterLite base
URL, then package ``file_name`` values are resolved against the lock URL.
Wheels live in ``dist/pypi/`` and the lock lives in ``dist/static/``, so a
local wheel is ``../pypi/<filename>``.
"""

from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
WHEEL_DIR = DIST / "pypi"
LOCK_PATH = DIST / "static" / "pyodide-lock.json"
CACHE_DIR = ROOT / ".cache" / "wheels"
CDN = "https://cdn.jsdelivr.net/pyodide/v314.0.6/full/"
CDN_LOCK = CDN + "pyodide-lock.json"
SITE_LOCK = "https://play.molcrafts.org/static/pyodide-lock.json"

# name, version, imports, lock dependencies, filename, sha256, url
PACKAGES: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], str, str, str], ...] = (
    (
        "websockets",
        "15.0.1",
        ("websockets",),
        (),
        "websockets-15.0.1-py3-none-any.whl",
        "f7a866fbc1e97b5c617ee4116daaa09b722101d4a3c170c787450ba409f9736f",
        "https://files.pythonhosted.org/packages/fa/a8/5b41e0da817d64113292ab1f8247140aac61cbf6cfd085d6a0fa77f4984f/websockets-15.0.1-py3-none-any.whl",
    ),
    (
        "molcrafts-mollog",
        "1.3.1",
        ("mollog",),
        ("rich",),
        "molcrafts_mollog-1.3.1-py3-none-any.whl",
        "113da22d79bdb9529c6647ee2db8a6a4656bdd5e69aa2214d2ddb29b0a74a6b3",
        "https://files.pythonhosted.org/packages/4c/6d/d3d9d1d6932ce5101dd86cf18d4cfc29e8616e57bd8989aab710b5217550/molcrafts_mollog-1.3.1-py3-none-any.whl",
    ),
    (
        "molcrafts-molcfg",
        "1.5.1",
        ("molcfg",),
        ("pyyaml",),
        "molcrafts_molcfg-1.5.1-py3-none-any.whl",
        "405d2a991352666afc16dec99fde37c3b81e265a17d6be0896d02141200b284b",
        "https://files.pythonhosted.org/packages/93/b5/2cf85c485d53097cf2a3a765ab844e1812623b8c2649fe0ea58346f9b89c/molcrafts_molcfg-1.5.1-py3-none-any.whl",
    ),
    (
        "molcrafts-molpy",
        "0.17.0",
        ("molpy",),
        ("numpy", "molcrafts-molrs", "molcrafts-mollog", "molcrafts-molcfg"),
        "molcrafts_molpy-0.17.0-py3-none-any.whl",
        "4efe7bfeff0e3d2678ea498dc9ffd4ac0d15c5fea32b1b3be26869d6aef58d15",
        "https://files.pythonhosted.org/packages/4e/5c/5893c3b1241dd52e4019871b95f90c0d15d01f5f78975f616a6c0badc157/molcrafts_molpy-0.17.0-py3-none-any.whl",
    ),
    (
        "molcrafts-molrs",
        "0.17.0",
        ("molrs",),
        ("numpy",),
        "molcrafts_molrs-0.17.0-cp312-abi3-pyemscripten_2026_0_wasm32.whl",
        "192ebff2723f81f06dff7c6f57dff7f4371e4caca9a167b74cc74d5f8f2df298",
        "https://files.pythonhosted.org/packages/aa/42/1cc6ee3129b5e4a4693b5a11a78f9100ff910f5dc3389fb30c2af0627e45/molcrafts_molrs-0.17.0-cp312-abi3-pyemscripten_2026_0_wasm32.whl",
    ),
    (
        "molcrafts-molvis",
        "0.3.0",
        ("molvis",),
        ("molcrafts-molpy", "numpy", "websockets"),
        "molcrafts_molvis-0.3.0-py3-none-any.whl",
        "0514e09a2d9ef0d96fdbb1f36cff66a485512b9cd10c8bcfaca13ad2b6b01aa4",
        "https://files.pythonhosted.org/packages/90/55/281f0e7c8b9e54606a741a8ef0fa925a44bc7b5c303d043e6170a96b5dd4/molcrafts_molvis-0.3.0-py3-none-any.whl",
    ),
)


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "molcrafts-playground-build"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _wheel(filename: str, url: str, sha256: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    WHEEL_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / filename
    if cached.is_file() and _sha256(cached.read_bytes()) == sha256:
        data = cached.read_bytes()
    else:
        data = _fetch(url)
        digest = _sha256(data)
        if digest != sha256:
            raise SystemExit(f"{filename}: sha256 {digest} != {sha256}")
        cached.write_bytes(data)
    target = WHEEL_DIR / filename
    if not target.is_file() or _sha256(target.read_bytes()) != sha256:
        target.write_bytes(data)


def _load_cdn_lock() -> dict:
    data = _fetch(CDN_LOCK)
    lock = json.loads(data)
    info = lock.get("info") or {}
    if info.get("abi_version") != "2026_0" or info.get("python") != "3.14.2":
        raise SystemExit(f"unexpected Pyodide lock info: {info}")
    return lock


def _rewrite_cdn(packages: dict) -> None:
    for name, entry in packages.items():
        file_name = entry.get("file_name")
        if not isinstance(file_name, str) or file_name.startswith(("https://", "http://")):
            continue
        if "/" in file_name:
            raise SystemExit(f"{name}: unexpected relative file_name {file_name}")
        entry["file_name"] = CDN + file_name


def _check_lite_config() -> None:
    config_path = DIST / "jupyter-lite.json"
    config = json.loads(config_path.read_text())
    settings = (
        config.get("jupyter-config-data", {})
        .get("litePluginSettings", {})
        .get("@jupyterlite/pyodide-kernel-extension:kernel", {})
        .get("loadPyodideOptions", {})
    )
    if settings.get("lockFileURL") != "./static/pyodide-lock.json":
        raise SystemExit(
            "dist/jupyter-lite.json is missing lockFileURL ./static/pyodide-lock.json. "
            "Re-run `jupyter lite build` so it picks up jupyter-lite.json."
        )


def main() -> None:
    if not (DIST / "jupyter-lite.json").is_file():
        raise SystemExit("dist/jupyter-lite.json is missing. Run `jupyter lite build` first.")
    _check_lite_config()

    lock = _load_cdn_lock()
    packages = lock["packages"]
    _rewrite_cdn(packages)
    for dep in ("numpy", "rich", "pyyaml", "micropip"):
        if dep not in packages:
            raise SystemExit(f"Pyodide lock is missing {dep}")

    for name, version, imports, depends, filename, sha256, url in PACKAGES:
        if name in packages:
            raise SystemExit(f"{name} is already in the Pyodide lock")
        for dep in depends:
            if dep not in packages and dep not in {item[0] for item in PACKAGES}:
                raise SystemExit(f"{name} depends on {dep}, which is not in the lock")
        _wheel(filename, url, sha256)
        resolved = urllib.parse.urljoin(SITE_LOCK, f"../pypi/{filename}")
        expect = f"https://play.molcrafts.org/pypi/{filename}"
        if resolved != expect:
            raise SystemExit(f"{filename} resolves to {resolved}, want {expect}")
        packages[name] = {
            "depends": list(depends),
            "file_name": f"../pypi/{filename}",
            "imports": list(imports),
            "install_dir": "site",
            "name": name,
            "package_type": "package",
            "sha256": sha256,
            "unvendored_tests": False,
            "version": version,
        }

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(lock, separators=(",", ":")) + "\n")
    print(f"wrote {LOCK_PATH} ({len(packages)} packages)")
    print(f"wrote {len(PACKAGES)} wheels to {WHEEL_DIR}")


if __name__ == "__main__":
    main()
