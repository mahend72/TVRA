# AI Assurance Perspective

This document positions the AI-assisted components of this repository
(`Final_Files`, and the single OpenAI vision call in
`deployment/src/medsec/api.get_plot_threat_model`) within an AI Assurance
framing: reliability, groundedness, robustness, security, traceability,
uncertainty, reproducibility, human oversight, and accountability.

The scope is narrow on purpose: only two things in this repository actually
call a machine-learning model — the threat/mitigation LLM calls in
`Final_Files`, and the one hardcoded OpenAI vision call in the TVRA core
API. The rest of the repository (OpenVAS scanning, SpydeRisk risk
calculation, centralDB evidence storage, O-ETB assurance-case logic) is
deterministic, rule-based tooling that this AI layer sits on top of and
draws evidence from. That surrounding tooling is itself a natural fit for
demonstrating **traceability** and **human oversight** properties, even
though it contains no learned model.

No claim in this document should be read as "this system is safe/robust" —
each row states what is actually evidenced in the code, and what is not.

## Capabilities demonstrated vs. properties evaluated vs. future extensions

- **Capabilities demonstrated by the existing project**: automated
  vulnerability scanning and structured risk modelling (OpenVAS +
  SpydeRisk); LLM-based augmentation of a threat list and generation of
  per-threat mitigation text; versioned, hash-verified evidence storage;
  a working example of an assurance-case claim gated on evidence validation
  (O-ETB).
- **Assurance properties actually evaluated (i.e. with a test or check in
  this repo)**: deterministic configuration/validation logic
  (`tests/test_model_config.py`, `tests/test_tvra_asset_parsing.py`,
  `tests/test_lib_openvas_target_validation.py`), evidence-not-found error
  messages (`tests/test_evidence_exceptions.py`), and the threat
  simplification/sorting logic that turns raw SpydeRisk output into a
  reported risk list (`tests/test_api_threat_simplification.py`).
- **Potential future assurance extensions**: LLM-output schema validation,
  automated citation checking, prompt-injection test cases, authenticated
  access control, structured logging/audit trails for LLM calls. These are
  listed as gaps below, not implemented.

## Assurance property table

| Assurance Property | What it means here | Existing evidence | Artifact/Test | Current gap |
|---|---|---|---|---|
| **Reliability** | The threat-model and mitigation endpoints return a usable result (or a clear error) for a given input | Both endpoints catch exceptions from the LLM client and return an HTTP error rather than crashing (`threat_model_endpoint.py`, `Mitigation_endpoint_remote.py`); mitigation results are flushed to disk after *every* threat, not just at the end, so a mid-run failure does not lose prior results (`Mitigation_endpoint_remote.write_json`) | `Final_Files/Mitigation_endpoint_remote.py: mitigate()` | No retry/backoff on transient provider errors; no test exercises the actual LLM call path (it is not mocked anywhere in `tests/`) |
| **Groundedness** | Generated threats/mitigations are tied to the actual input threat model, not invented from nothing | The prompt explicitly includes the caller's threat model / already-detected threats and instructs the model to return only *new* items (`prompts.py`); the mitigation prompt includes the specific threat JSON object being mitigated | `Final_Files/prompts.py`, `Mitigation_endpoint_remote.py: PER_THREAT_PROMPT` | No check that the LLM's output actually corresponds to the supplied input (e.g. no verification that a returned "threat" matches a real element of the threat model); no retrieval-augmentation or citation verification against the ISO/OWASP/NIST references it is asked to use |
| **Robustness** | Behaviour under malformed, adversarial, or out-of-distribution input | `check_valid_target` validates scan targets before use; `secure_filename` sanitises evidence filenames; `get_mitigation` falls back to raw text if the LLM's response is not valid JSON rather than crashing (`Mitigation_endpoint_remote.py`) | `tests/test_lib_openvas_target_validation.py` | No test coverage for malformed/adversarial *threat model* or *image* input reaching the LLM-calling paths; no defence against prompt injection (see [THREAT_MODEL.md](THREAT_MODEL.md)) |
| **Security** | Access control, key handling, and injection resistance around the AI-calling code | Localhost/127.0.0.1 base URLs are rejected at configuration time (`config.py: ModelConfig.__post_init__`) | `tests/test_model_config.py: test_model_config_rejects_localhost_endpoints` | No authentication on the endpoints that trigger LLM calls; API keys are caller-supplied per request rather than held server-side; no prompt-injection defences — full analysis in [THREAT_MODEL.md](THREAT_MODEL.md) |
| **Traceability** | Evidence and results can be traced back to their source and to a point in time | centralDB stores every evidence artefact with a category, filename, version number, timestamp, comment, and SHA-256 hash (`centralDB/app/storage.py`); the O-ETB example agent demonstrates pulling that evidence to validate a specific assurance-case claim (`Assurance/build/files/KB/AGENTS/simple_agent.pl`) | `tests/test_evidence_exceptions.py`; `centralDB/README.md` data-flow diagrams | LLM calls themselves are not logged as evidence with the same rigor (no request/response hash, no record of which model/provider/version produced a given mitigation string beyond what the caller supplied in the request) |
| **Uncertainty** | Whether the system communicates confidence or ambiguity in its outputs | None found. LLM responses are returned as plain strings; no confidence score, no indication of model disagreement, no flag distinguishing "the model found nothing new" from "the model failed to respond usefully" beyond the JSON-parse-failure fallback | — | This is an open gap, not a partially-implemented feature |
| **Reproducibility** | Given the same input and configuration, results can be regenerated or at least understood after the fact | Deterministic components (config validation, TVRA model parsing, risk-level sorting) are fully covered by `tests/` and are reproducible by construction; the CI workflow runs the full suite on every push (`.github/workflows/ci.yml`) | `tests/` (29 tests, see [REPRODUCIBILITY.md](../REPRODUCIBILITY.md)) | LLM-generated output is inherently non-deterministic (`temperature` defaults to `0.7` in every provider template in `config.py`) and provider/model versions are not pinned in evidence — the same request will not reliably reproduce the same mitigation text |
| **Human oversight** | A human can review, override, or gate an AI-influenced decision | The O-ETB assurance-case model is oversight-by-construction: a claim is only `valid` once its evidence passes an agent check, and `BUILD_GUIDE.md` documents a human review step for changes to the shared knowledge base ("run by me any proposed changes... before committing them") | `Assurance/build/BUILD_GUIDE.md`; `Assurance/build/files/KB/PATTERNS/pattern_simple.pl` | This oversight model exists for the assurance-case layer in the private upstream O-ETB workflow, not as an in-repository gate on the LLM-generated mitigation text itself before it is stored as evidence — nothing here blocks an LLM mitigation string from being uploaded to centralDB without review |
| **Accountability** | It is possible to attribute an output or decision to a specific actor, run, or input | Evidence uploads record a `comment` field and timestamp; git history attributes code changes to a committer | `centralDB/app/storage.py` (`comment`, `timestamp` fields) | No caller identity is recorded anywhere (all endpoints are unauthenticated — see [THREAT_MODEL.md](THREAT_MODEL.md)), so an evidence record can be timestamped but not attributed to a person or service account |

## Summary

The strongest AI-assurance property demonstrated by this repository is
**traceability of evidence** — the evidence-store-plus-assurance-case
pattern (centralDB + O-ETB) is a genuine, working implementation of
"a claim is valid only if backed by recorded, hash-verified evidence." The
weakest properties are **uncertainty communication** (none) and
**accountability for the LLM-calling paths specifically** (no caller
identity, no per-call audit record separate from what the caller chose to
submit). Anyone building on this repository for an AI Assurance case should
treat the LLM-generated threat/mitigation text as **unverified analyst
input requiring human review**, not as a validated security control — that
review step exists in the O-ETB pattern for other evidence categories, but
is not yet wired to the AI-generated output produced by `Final_Files`.
