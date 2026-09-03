# Reproducibility

This document explains what can and cannot currently be reproduced from this
repository alone, and exactly how to reproduce the parts that can be.

There is no single "main experiment" with a fixed dataset and expected
numeric result — this is a software toolkit, not a benchmark paper. What
*is* reproducible is (a) the deterministic test suite, and (b) running each
service and exercising it against the sample data in `docs/`. Where full
end-to-end reproduction is not currently possible from this repository
alone, that is stated explicitly, with the reason.

## What you can reproduce today

### 1. The test suite (fully reproducible, no external services required)

**Supported OS:** any OS that runs Python 3.11 (the test suite itself has no
Linux-specific code; CI runs it on `ubuntu-latest`). The full Docker stack
(below) requires Linux, per
[docs/LIMITATIONS.md](docs/LIMITATIONS.md#hardware-and-deployment-assumptions).

**Python version:** 3.11 (pinned in `.github/workflows/ci.yml`; no other
version has been verified).

**Environment creation:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

This installs only `pytest`, which is enough to run 21 of the 26 test
functions across 5 files (the ones with no heavy third-party dependency).
To run the full suite, including the OpenVAS-target-validation and
threat-simplification tests, also install the TVRA core API's dependencies:

```bash
pip install -r deployment/src/requirements.txt
```

**Commands:**

```bash
python -m pytest tests/ -v
```

**Expected output:** all tests pass (some are skipped instead of failing if
`deployment/src/requirements.txt` was not installed — see
`tests/test_lib_openvas_target_validation.py` and
`tests/test_api_threat_simplification.py`, which use `pytest.importorskip`
for exactly this reason).

**Random seeds:** not applicable — every test in `tests/` is deterministic
(pure functions, dataclass parsing, config validation; no model inference,
no randomness).

**Result files:** none are produced; this is a pass/fail test run, not an
experiment producing output artefacts.

### 2. Running the services individually against sample data

Each service can be started and exercised against the corresponding sample
file already committed under `docs/` or `centralDB/sample/`, without needing
the full Docker stack:

| Service | How to start | Sample input | What to try |
|---|---|---|---|
| `centralDB` (Evidence Manager) | `cd centralDB && pip install -r requirements.txt && uvicorn app.main:app --reload` (needs a writable `/app/data`, or adjust `DATA_DIR` in `app/storage.py` for local use) | `centralDB/sample/get_threats_OUTPUT.json` | `POST /upload-json/threats` with that file's content, then `GET /list/threats` |
| `Final_Files` (AI threat/mitigation) | `cd Final_Files && pip install -r requirements.txt && ./start_services.sh` | `Final_Files/get_threats_OUTPUT.json`, `Final_Files/threat_model.json` | `python threat_model_client.py` / `python Mitigation_client.py` (edit the placeholder `api_key` in each script's `__main__` block first, or pass your own) |

**Model versions:** the LLM model used for `Final_Files` is whatever you
select via the `provider`/`model_name` request fields; the defaults in
`Final_Files/config.py: PROVIDER_TEMPLATES` (e.g. `gpt-4o-mini`,
`claude-3-haiku-20240307`) are placeholders, not a pinned, evaluated model
version — see [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

**Required external services for this path:** a reachable, non-localhost
endpoint for your chosen LLM provider, and a valid API key for it (except
for `custom_ollama`, which needs a reachable Ollama instance instead of a
key). No API key is bundled with this repository, and none should ever be
committed to it (see [SECURITY.md](SECURITY.md)).

## What requires the full Docker stack (Linux only)

The TVRA core API's vulnerability scanning depends on the compiled OpenVAS
stack in `deployment/Dockerfile` (`gvm-libs`, `openvas-scanner`,
`ospd-openvas`), and its threat/risk features depend on a running SpydeRisk
System Modeller plus Keycloak (`deployment/docker-compose.yml`). To
reproduce that path:

```bash
cd deployment
cp .env.example .env   # then edit — see SECURITY.md before changing defaults
./deploy_tvra.sh        # or: docker compose -f docker-compose.yml up --build
```

**Approximate hardware requirements:** not independently verified in this
repository. `deployment/docker-compose.yml` runs SpydeRisk (a JVM
application with its own Jena TDB store), Keycloak, an nginx proxy, and the
TVRA/OpenVAS container together; expect this to need a multi-GB-RAM Linux
host. No specific number is documented upstream in this repository, so none
is stated here — see `docs/user_guide.md` for any additional operational
notes, and treat sizing as something to determine empirically for your
environment rather than a number this document can responsibly assert.

**Required services:** Docker, Docker Compose, a Linux host (see
[docs/LIMITATIONS.md](docs/LIMITATIONS.md)).

## What is currently *not* reproducible from this repository alone

- **The Assurance / O-ETB assurance-case example.**
  `Assurance/build/Dockerfile` expects an externally-supplied `Assurance/`
  directory containing the O-ETB engine itself (`COPY Assurance /Assurance`).
  Per `Assurance/build/BUILD_GUIDE.md`, that engine is maintained in a
  private upstream repository (`MedSecurance/Assurance`) that is not part of
  this repository and not publicly accessible. **What is missing:** the
  O-ETB `src/`/`BUILD/` Prolog engine. **What this repository does provide**
  that can be reviewed without that engine: the Knowledge Base contribution
  itself (`Assurance/build/files/KB/`) and the Python evidence-gateway
  script it calls (`simple_gateway.py`), which only depends on a running
  `centralDB` instance and can be read/tested independently of O-ETB.
- **A pinned, evaluated LLM model/provider configuration.** As noted above,
  no specific provider/model/temperature combination in this repository is
  presented as "the" validated configuration — every run of the AI-assisted
  services is only as reproducible as the chosen provider's own model
  stability and your `temperature` setting (default `0.7` in every
  provider template, i.e. non-deterministic by design).
- **Numeric risk scores from SpydeRisk/OpenVAS on data not included here.**
  The example JSON outputs under `docs/` and `centralDB/sample/` were
  produced by a specific, undocumented run (target host, scan feed version,
  and SpydeRisk model version are not recorded alongside them) and should be
  treated as illustrative samples, not as a reproducible benchmark result.

## Which result files correspond to which experiments

| File | Produced by |
|---|---|
| `docs/get_threats_OUTPUT.json`, `centralDB/sample/get_threats_OUTPUT.json`, `Final_Files/get_threats_OUTPUT.json` | `GET /v1/threat/get_threats` (simplified form) against a SpydeRisk model — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| `docs/get_threats_raw_mode_OUTPUT.json` | Same endpoint with `raw=true` |
| `docs/get_recommendation_full_OUTPUT.json` | `GET /v1/threat/get_recommendations` |
| `docs/get_attack_path_plot_OUTPUT.svg` | `GET /v1/threat/{model_id}/plot` |
| `docs/vuln_scanner_get_report_OUTPUT.{html,json}` | `GET /v1/report/{scanid}/{html,json}` (OpenVAS) |
| `docs/IoMT_Model_INPUT.json` | Example input to `PUT /v1/model/{name}` (TVRA model import) |
| `Assurance/build/files/KB/AGENTS/get_threats_OUTPUT.json` | Sample evidence used by `simple_gateway.py`'s JSON-upload test |
