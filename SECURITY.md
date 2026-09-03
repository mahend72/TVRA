# Security Policy

## Reporting a vulnerability

If you find a security issue in this project, please open a private report
via GitHub's "Report a vulnerability" feature on this repository (Security
tab → Advisories), rather than a public issue. Include reproduction steps and
the affected component (TVRA API, centralDB, Assurance/O-ETB, or the
deployment stack).

## Known, intentional insecure defaults (development only)

This repository bundles a **development-only** Keycloak realm
(`deployment/spyderisk/provisioning/keycloak/ssm.template`) used to bootstrap
an isolated local Spyderisk deployment. It ships with a publicly documented
default account (`testadmin` / `password`, see `docs/user_guide.md`) and a
placeholder `KEYCLOAK_CREDENTIALS_SECRET` that is substituted from your `.env`
file at container start (see `deployment/spyderisk/provisioning/keycloak/entrypoint.sh`).

This is **not** suitable for anything beyond local development or a fully
isolated lab network:

- Change `KEYCLOAK_ADMIN_USERNAME`, `KEYCLOAK_ADMIN_PASSWORD`, and
  `KEYCLOAK_CREDENTIALS_SECRET` in your own `.env` before exposing any
  instance beyond localhost (see `deployment/.env.example`).
- Do not reuse the bundled `ssm.template` realm export as-is in anything
  reachable from an untrusted network.
- Rotate the Keycloak realm secret and disable/replace the `testadmin`
  account before any shared or production-like deployment.

## AI provider credentials

Components under `Final_Files/` accept API keys for third-party LLM providers
(OpenAI, Anthropic, Azure OpenAI, Groq, Together AI, etc.) at request time —
see `Final_Files/config.py`. These keys are never hardcoded in this
repository; provide them via your own environment/secret store and never
commit them.

## Responsible use

This toolkit performs active vulnerability scanning (OpenVAS) and produces
risk assessments intended for systems you own or are explicitly authorized to
test. Do not scan or assess third-party infrastructure without permission.
