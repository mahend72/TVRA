# Threat Model

This is a practical, code-derived threat model for the components in this
repository. Every claim below is anchored to a specific file; where a
mitigation is described, that is because the corresponding code exists —
nothing here is aspirational. Labels: **Implemented**, **Partial**, **Not
implemented**, **Future work**.

This complements [SECURITY.md](../SECURITY.md), which covers vulnerability
reporting and the previously-documented Keycloak/AI-credential handling
notes. This document goes further into per-component analysis.

## 1. System scope

In scope: the TVRA core API, centralDB, the `Final_Files` AI-assisted
services, and the O-ETB example agent/gateway, as implemented in this
repository. Out of scope: the internals of OpenVAS/Greenbone, SpydeRisk
System Modeller, Keycloak, and the private O-ETB engine itself — these are
third-party/external systems this repository integrates with, not code
this repository controls.

## 2. Assets

| Asset | Where | Sensitivity |
|---|---|---|
| Vulnerability scan results | OpenVAS reports, centralDB | Reveals exploitable weaknesses of the assessed system |
| Risk/threat models | SpydeRisk, centralDB, `docs/*OUTPUT.json` | Reveals system architecture and its weakest points |
| LLM-generated threats/mitigations | `Final_Files`, `mitigation_outputs/` | Same sensitivity as the input threat data; also a source of possible hallucinated guidance (see [AI_ASSURANCE.md](AI_ASSURANCE.md)) |
| Assurance-case evidence and verdicts | centralDB, O-ETB `REPOSITORY/` | Basis for a compliance/assurance claim; integrity matters more than confidentiality |
| LLM provider API keys | In-flight, in `Final_Files` request bodies | Credential with billing/usage impact if leaked |
| SpydeRisk/Keycloak credentials | Hardcoded in `lib_spyderisk.py`; `deployment/.env` | Access to the risk model service |
| SSH credentials for scan targets | `schema.Scan.sshuser/sshpass/sshkey`, in-flight to the TVRA API | Access to scanned hosts |

## 3. Threat actors

- **Unauthenticated network client** — anyone who can reach an exposed
  service port. Given none of the FastAPI services in this repository
  implement authentication, this is the most relevant actor for every
  endpoint listed in [ARCHITECTURE.md](ARCHITECTURE.md).
- **Malicious or careless evidence contributor** — someone able to write to
  centralDB or the O-ETB `KB/` mount, e.g. an insider or a compromised
  upstream tool.
- **Compromised/malicious remote LLM provider or man-in-the-middle** — the
  provider named in a `Final_Files` request, or anything between this
  service and that provider.
- **Malicious scan target** — a host being scanned that returns malformed or
  adversarial data.

## 4. Trust boundaries and entry points

| Boundary | Entry point | Authentication present? |
|---|---|---|
| Network → TVRA core API | All `/v1/*` routes, `deployment/src/medsec/main.py` | **No** |
| Network → centralDB | All routes, `centralDB/app/main.py` | **No** |
| Network → `Final_Files` AI endpoints | `/process-threat-model`, `/mitigate`, `/mitigate_legacy` | **No** |
| Network → Assurance API shim | `Assurance/build/files/api/main.py` | **No** |
| TVRA core API → SpydeRisk | `lib_spyderisk.py`, hardcoded `testadmin`/`password` | Yes, to SpydeRisk, but with a hardcoded, publicly-documented dev account |
| TVRA core API → OpenVAS | Unix socket, same container | Local IPC only, not network-exposed |
| `Final_Files` → remote LLM provider | `remote_ai_client.py` | Yes, via per-request API key |

## 5. Attacker assumptions

The attacker can reach any port that is exposed by the deployment's
Docker/Kubernetes network policy or reverse proxy configuration. This
document assumes **no additional network-layer access control** beyond what
is described in `deployment/docker-compose.yml` and
`centralDB/README.md`'s stated intent ("no direct external access to
centralDB") — that intent is a deployment-time network policy, not something
enforced by the application code itself.

## 6. Threats, by category

### Prompt injection / indirect prompt injection

**Not implemented.** `threat_model_endpoint.py` and
`Mitigation_endpoint_remote.py` interpolate caller-supplied JSON directly
into the LLM prompt (`prompts.py: threat_json_prompts`,
`Mitigation_endpoint_remote.py: PER_THREAT_PROMPT`) with no sanitisation,
delimiter escaping, or instruction-hierarchy defence. `api.get_plot_threat_model`
(`deployment/src/medsec/api.py`) sends a generated image to the OpenAI
vision API and trusts its textual output as the threat report. Since the
LLM's output is written back as "evidence" (mitigation strategy, threat
report), a manipulated threat-model JSON or attack-path image is a plausible
route to influencing what gets recorded as a security recommendation.

### Poisoned retrieval / knowledge-base manipulation

**Partial.** O-ETB assurance-case patterns and validation agents (Prolog,
under `Assurance/build/files/KB/`) define what counts as valid evidence.
`BUILD_GUIDE.md` documents a human-review process for the upstream private
repository ("run by me any proposed changes to files in src before
committing them"), but there is no technical control in *this* repository
(no code signing, no automated review gate) preventing a party with write
access to a deployed `KB/` mount from redefining a pattern or agent so that
weaker evidence — or no evidence — is accepted as `valid`.

### Insecure model/API interaction

**Partial.** LLM provider selection, model name and API key are supplied
per request rather than being pinned server-side
(`Final_Files/config.py: create_model_config`). Combined with the lack of
authentication on `/process-threat-model` and `/mitigate` (see above), any
network client that can reach these endpoints can direct the service to call
any supported provider using a key of the client's choosing — effectively an
open relay for LLM calls billed to whatever key is supplied, at this
service's expense of compute/network. `ModelConfig.__post_init__` blocks the
literal strings `localhost`/`127.0.0.1`/`http://localhost`/`http://127.0.0.1`
as `base_url` values; it does **not** block other internal addresses (RFC1918
ranges, `169.254.169.254`, `.internal` DNS names), so this is not an SSRF
control despite superficially resembling one.

### Malicious or malformed inputs

**Partial.** `schema.Scan.target` is validated via
`lib_openvas.check_valid_target` (IP address or DNS syntax). Uploaded
filenames in centralDB are passed through `secure_filename()`
(`centralDB/app/storage.py`), which strips characters outside
`[\w.-]` — this defeats path-traversal via `/`. The `category` path segment
is not separately validated at the application layer; its safety currently
relies on FastAPI/Starlette's default single-segment path matching (no `/`
in a plain `{category}` parameter) rather than an explicit check. Threat
model / mitigation payload sizes are unbounded — no request size limit is
configured on any service.

### Unauthorised access

**Not implemented.** None of the four FastAPI services enforce
authentication or authorisation. `deployment/src/medsec/main.py` additionally
sets `CORSMiddleware` with `allow_origins=["*"]` and
`allow_credentials=True`, a combination most browsers reject but that
signals the intended posture was never "restrict origins."

### Secret exposure

**Partial.**
- LLM API keys travel in JSON request bodies (`Final_Files`), not in an
  `Authorization` header or a server-side secret store; they are held only
  in memory for the duration of the call (no disk persistence found), but
  they do cross the network boundary with each call and are visible to
  anything that can observe or log that request.
- SpydeRisk/Keycloak dev credentials (`testadmin`/`password`) are hardcoded
  in `deployment/src/medsec/lib_spyderisk.py` and its call sites, not read
  from configuration — `SECURITY.md` documents the account as a known,
  intentional dev-only default, but rotating it in Keycloak alone would not
  remove it from the source.
- `.gitignore` excludes `.env`, `*.pem`, `*.key`, `*credentials*.json`,
  `*secret*`; a scan of this repository's tracked files at the time of
  writing found no committed real secrets, only clearly-labelled placeholder
  values (`deployment/.env.example`, `CONFIGURATION.md`).

### Unsafe tool execution

**Partial.** `lib_openvas.run_monitor_scan_progress` calls
`subprocess.Popen(command)` with `command` built as a Python list (not
`shell=True`), which prevents classic shell-metacharacter injection.
However, the `name` argument (a caller-chosen scan identifier) is not
validated the way `scan.target` is, before being passed as a CLI argument
to the monitoring script. `simple_agent.pl` (O-ETB) invokes
`shell(Command, ResultCode)` with a hardcoded command string — not
attacker-influenced input — so this specific call site is not currently
exploitable via network input.

### Data poisoning / provenance failure

**Partial.** centralDB computes a SHA-256 hash at upload time and
re-verifies it before returning a file on download
(`centralDB/app/storage.py`, `centralDB/app/main.py`), which detects
accidental corruption or storage-layer tampering. It does **not** protect
against a party with API write access uploading a new version with
attacker-controlled content and a self-consistent hash — there is no
separate, harder-to-forge provenance record (no signing key, no append-only
or externally-witnessed log of hash history).

### Hallucinated security claims

**Not implemented.** Mitigation and threat-analysis text is generated by an
LLM and asked to "reference ISO/OWASP/NIST"
(`Final_Files/Mitigation_endpoint_remote.py: SYSTEM_MSG`,
`Final_Files/prompts.py`), but nothing in the code checks that a cited
control or standard reference is real, current, or actually applicable
before the text is stored as evidence or returned to a caller. See
[AI_ASSURANCE.md](AI_ASSURANCE.md) for the groundedness discussion.

### Compromised external services

**Future work.** If OpenVAS, SpydeRisk, Keycloak, or a remote LLM provider
returns unexpected or adversarial data, the current code generally either
propagates an HTTP error (SpydeRisk/OpenVAS paths mostly do) or, for LLM
responses that fail to parse as JSON, falls back to returning the raw text
as the "mitigation strategy" (`Mitigation_endpoint_remote.get_mitigation`) —
there is no independent verification step.

### Audit-log integrity

**Not implemented.** Application logs are written to a local, mutable file
(`logger.py`, default `medsec.log`, mode `"a"`) and to stdout. Unlike
evidence files in centralDB, log entries are not hashed, signed, or written
to an append-only/externally-witnessed store, so log tampering after the
fact would not be detectable from within this repository's code.

## 7. Residual risks (summary)

Given the above, the realistic residual risk for a deployment that follows
only what is in this repository (no additional network policy, gateway
authentication, or secret management layered on top) is: **any network
client that can reach a service port can read and write evidence, trigger
scans against arbitrary-looking targets, and drive LLM calls using a key of
its choosing.** `centralDB/README.md`'s stated architecture ("no direct
external access to centralDB") and `SECURITY.md`'s guidance ("suitable only
for local development or a fully isolated lab network") describe the
intended compensating control — network isolation — which must be provided
by the deployer, since it is not enforced in this codebase.

## 8. Recommended near-term mitigations (not yet implemented)

These are suggestions, not claims about the current state:

1. Add authentication (at minimum, a shared API key or mTLS between internal
   services) to all four FastAPI services before any deployment beyond an
   isolated lab network.
2. Move LLM provider API keys to server-side configuration/secrets and stop
   accepting them as caller-supplied request fields, or at least require the
   caller to be authenticated first.
3. Replace the CORS wildcard in `deployment/src/medsec/main.py` with an
   explicit allow-list.
4. Replace the hardcoded SpydeRisk credentials with environment-sourced
   configuration, consistent with how `deployment/.env.example` already
   handles Keycloak's own credentials.
5. Add request size limits and basic rate limiting at the reverse proxy or
   application layer.
6. Add schema validation for LLM output before it is persisted as
   "mitigation" evidence, and consider a citation/reference check against a
   known control list.
