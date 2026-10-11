# molcrafts-playground

JupyterLite site for the MolCrafts packages that run in Pyodide. Hosted on
Cloudflare Pages.

Public URL: <https://play.molcrafts.org/>

`play` is a function hostname, same shape as `docs` and `app`. The repo name
stays `molcrafts-playground`. The site is attached to Pages as a custom
domain, at the origin root, so the JupyterLite service worker and the
COOP/COEP headers apply without a path prefix.

## What the kernel has

| Package | How it gets into the browser |
| --- | --- |
| molpy 0.17.0 | pure-Python wheel |
| molrs 0.17.0 | Pyodide wheel pulled in by molpy |
| mollog, molcfg | pure-Python wheels pulled in by molpy |
| numpy | Pyodide's own build |
| molvis 0.3.0 | pure-Python wheel |
| websockets 15.0.1 | pure-Python wheel, required by molvis |

Pyodide itself is loaded from the jsDelivr CDN. It is not vendored into the
Pages upload (single-file limit 25 MiB).

`jupyterlite-pyodide-kernel` can build a custom lock with `pyodide-lock`, but
that tool still calls `uv` with `--python-platform=wasm32-pyodide2024`. uv
0.13 has no `wasm32-pyodide2026` platform, and molrs 0.17 publishes
`pyemscripten_2026_0_wasm32`. `scripts/extend_lock.py` copies the Pyodide
314.0.6 lock, rewrites its package URLs to jsDelivr, and appends the wheels
above. The kernel preloads them through `loadPyodideOptions`.

`mv.Stage()` needs a local WebSocket host. That call does not run in this
kernel. Structure coercion and palette rendering do. The interactive viewer
is [app.molcrafts.org/molvis/](https://app.molcrafts.org/molvis/).

## Build

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
./scripts/build.sh
```

`scripts/build.sh` uses `.venv` when that directory already exists. On
Cloudflare Pages it installs `requirements.txt` with `pip`, then runs
`jupyter lite build`, `scripts/extend_lock.py`, and copies `_headers` into
`dist/`. The Pages build image reads `.python-version` and uses Python 3.12.

## Deploy

The Pages project `molcrafts-playground` is connected to this GitHub
repository. A push to `master` runs `./scripts/build.sh` and publishes
`dist/`. There is no GitHub Action and no direct upload.

Production: <https://molcrafts-playground.pages.dev/>

`play.molcrafts.org` is a custom domain on the `molcrafts-playground` Pages
project. It stays pending until the `molcrafts.org` zone has a CNAME from
`play` to `molcrafts-playground.pages.dev`.
