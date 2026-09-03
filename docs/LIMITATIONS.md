# Limitations

This document lists known scientific and engineering limitations of the
toolkit as it exists in this repository. It is intended to be read alongside
[THREAT_MODEL.md](THREAT_MODEL.md) (security-specific gaps) and
[AI_ASSURANCE.md](AI_ASSURANCE.md) (assurance-property gaps).

## Coverage and evaluation

- **No benchmark or ground-truth dataset.** There is no labelled set of
  "known threats/vulnerabilities" against which the LLM-assisted threat
  identification or OpenVAS scan results are measured for precision/recall.
  The `docs/*OUTPUT.json` files are example outputs from a single run, not
  an evaluation set.
- **No systematic evaluation of LLM output quality.** Nothing in this
  repository scores the correctness, completeness, or specificity of
  LLM-generated threats or mitigation text against a reference. The only
  automated checks on that code path are for the surrounding configuration
  logic (`tests/test_model_config.py`), not the model output itself.
- **Risk-level classification is domain-tuned but unvalidated.**
  `lib_spyderisk.calculate_the_risk` uses a hand-authored severity/QoD
  threshold table (`risk_matrix` in `deployment/src/medsec/lib_spyderisk.py`)
  to map OpenVAS severity scores to a trustworthiness level. This mirrors a
  reasonable manual triage heuristic but has not been validated against
  independent expert scoring.

## External and model dependence

- **Remote LLM providers are a hard external dependency for the AI-assisted
  paths.** `Final_Files` supports OpenAI, Anthropic, Azure OpenAI, Groq,
  Together AI, Hugging Face and remote Ollama, selected per request
  (`config.py`). Results, latency, and cost all depend on whichever
  provider/model the caller selects; the repository pins no specific model
  version as "the" evaluated configuration (default model names such as
  `gpt-4o-mini` and `claude-3-haiku-20240307` are placeholders in
  `PROVIDER_TEMPLATES`, not validated choices).
- **SpydeRisk System Modeller is an external, versioned dependency**
  (`deployment/docker-compose.yml` pins `SPYDERISK_VERSION`), maintained by
  IT Innovation, University of Southampton. This repository's risk
  calculation, recommendation, and attack-path features are only as correct
  as that upstream ontology/engine.
- **OpenVAS/Greenbone is built from pinned source versions**
  (`GVM_LIBS_VERSION`, `OPENVAS_SCANNER_VERSION`, `OSPD_OPENVAS_VERSION` in
  `deployment/Dockerfile`); vulnerability detection is limited to what that
  scanner's feed covers as of build time.
- **The O-ETB assurance-case engine is not included in this repository.**
  `Assurance/build/BUILD_GUIDE.md` states the core engine comes from a
  private upstream repository (`MedSecurance/Assurance`); only the
  contributed Knowledge Base example (`Assurance/build/files/KB/`) is
  present here. The Assurance/O-ETB component therefore cannot be built or
  run from this repository alone — see
  [REPRODUCIBILITY.md](../REPRODUCIBILITY.md).

## Generalisation

- **The one worked TVRA/SpydeRisk example is IoMT-flavoured.** Sample data
  (`docs/IoMT_Model_INPUT.json`) and prompt wording
  (`lib_spyderisk.py: vision_prompts` explicitly says "Consider the
  healthcare context") are tuned for a healthcare/IoMT scenario. Applying
  the toolkit to a materially different domain (e.g. industrial control
  systems) has not been demonstrated in this repository.
- **Asset/domain-kind mapping in `tvra_parser.py` is example-specific.**
  `network_domain_kind_mapping` and `tvra_asset_kind_mapping` are small,
  hand-maintained dictionaries; a TVRA model using kinds not already covered
  will parse but silently fall back to the unmapped value rather than
  raising an error, which needs a human check on unfamiliar models.

## Adversarial conditions

- **No adversarial testing of the LLM-calling paths** (prompt injection,
  adversarial images, malformed threat-model JSON). See
  [THREAT_MODEL.md](THREAT_MODEL.md) for the specific gaps.
- **No fuzzing or adversarial testing of the FastAPI input models.** Pydantic
  provides type-level validation only; there is no property-based or fuzz
  testing of `schema.py`/`Final_Files` request models in this repository.

## Security testing

- **No dependency vulnerability scan was run as part of this
  professionalisation pass beyond a manual grep-based secret scan** (see the
  session's final report for what that scan covered and found). CI now
  includes `pip-audit` for pip-installable dependencies (see
  [../.github/workflows/ci.yml](../.github/workflows/ci.yml)), but this does
  not cover the OS-level packages built into `deployment/Dockerfile` (e.g.
  `gvm-libs`, `openvas-scanner`).
- **No penetration testing has been performed against a running
  deployment.** The findings in [THREAT_MODEL.md](THREAT_MODEL.md) are from
  static code review, not from exercising a live instance.

## Dependency and version sensitivity

- **The four `requirements.txt` files pin genuinely incompatible versions
  of shared libraries** — most notably, `deployment/src/requirements.txt`
  requires `pydantic~=1.10` while `Final_Files/requirements.txt` requires
  `pydantic>=2.0.0`. This is a deliberate consequence of each service being
  a separate container, not an oversight, but it means the repository as a
  whole cannot be installed into a single Python environment. See
  [REPRODUCIBILITY.md](../REPRODUCIBILITY.md).
- **Version pinning style is inconsistent across services**: `Final_Files`
  uses `>=` lower bounds, `centralDB` uses exact `==` pins, and
  `deployment/src` uses `~=` compatible-release pins. None of the four are
  lock files (e.g. no hashes, no fully resolved transitive-dependency
  list), so a given install is not bit-for-bit reproducible over time even
  within one service.

## Hardware and deployment assumptions

- **The full stack assumes a Linux Docker host.** `deployment/Dockerfile`
  builds native code against Ubuntu 22.04 and expects to run OpenVAS
  scanning from inside that container; it is not intended to run natively
  on macOS/Windows. `docs/user_guide.md`/`README.md` both note this.
- **`host.docker.internal` is hardcoded** in
  `deployment/src/medsec/lib_spyderisk.py` and `api.py` as the SpydeRisk
  address, which works with Docker Desktop's built-in DNS alias but is not
  guaranteed on all Linux Docker setups without the `extra_hosts` mapping
  already present in `deployment/docker-compose.yml`.
- **No resource sizing guidance exists in this repository** for the OpenVAS
  scan engine or SpydeRisk beyond what upstream projects document; see
  [REPRODUCIBILITY.md](../REPRODUCIBILITY.md) for what can and cannot be
  stated about hardware requirements from the code alone.

## Large and generated files

These are the largest files currently tracked in the repository, classified
by what they are and what should eventually happen to them. None have been
moved or deleted as part of this pass — see [SECURITY.md](../SECURITY.md)
and the professionalisation report for why that decision is left to the
repository owner.

| File | Size | Classification | Recommendation |
|---|---|---|---|
| `docs/get_threats_raw_mode_OUTPUT.json` | 2.7 MB | Sample output (unprocessed SpydeRisk threat data) | Move to GitHub Releases or trim to a representative subset in `docs/`; keep only if it's actively used as a fixture |
| `docs/get_recommendation_full_OUTPUT.json` | 1.9 MB | Sample output | Same as above |
| `deployment/spyderisk/knowledgebases/domain-network-6a6-1-2.zip` | 840 KB | Deployment dependency (SpydeRisk domain ontology, loaded by `docker-compose.yml`) | Keep in-repo (it's a required build input, not incidental output) unless SpydeRisk starts publishing it as a versioned download, in which case fetch it at build time instead |
| `docs/get_threats_OUTPUT.json`, `centralDB/sample/get_threats_OUTPUT.json` | 231 KB each | Sample output / test fixture (two copies of the same example, in different roles — see [REPRODUCIBILITY.md](../REPRODUCIBILITY.md)) | Keep `centralDB/sample/` copy as a fixture; consider whether the `docs/` copy is redundant with it |
| `Final_Files/get_threats_OUTPUT.json` | 25 KB | Example input to `Final_Files` CLI clients | Keep — small, actively referenced by `threat_model_client.py`/`Mitigation_client.py` |
| `docs/get_attack_path_plot_OUTPUT.svg`, `docs/vuln_scanner_get_report_OUTPUT.{html,json}`, `docs/IoMT_Model_INPUT.json` | small | Sample output / input | Keep — small enough not to matter |

No file in the repository is a required research artifact in the sense of
"needed to reproduce a claimed result" (see
[REPRODUCIBILITY.md](../REPRODUCIBILITY.md) — there is no benchmark result
being claimed). The two multi-megabyte JSON files are the only ones worth
reconsidering; an `examples/` directory with a trimmed, representative
subset of each was not created in this pass because doing so without
input from the repository owner on which fields matter risks producing a
misleading "representative" sample.

## Testing scope

- **`tests/` covers pure, deterministic logic only** (configuration
  validation, TVRA JSON parsing, evidence error messages, target validation,
  threat simplification/sorting). It does not exercise any FastAPI endpoint
  end-to-end, does not start a live server, and does not mock or replay an
  LLM/OpenVAS/SpydeRisk call. This is a conscious scope choice (see
  `tests/conftest.py`'s docstring) rather than an oversight, but it means
  integration-level regressions (e.g. a broken HTTP route, a changed
  response shape) would not be caught by this suite.
