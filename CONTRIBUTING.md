# Contributing to tai42-accounts-oidc

`tai42-accounts-oidc` is the OIDC/OAuth2 login **accounts provider** for the TAI
ecosystem: session-based login via an external identity provider, sessions in
Redis, and the one-time SSO code hand-back to the SPA. The hard rule (the plugin
rule): **it depends on `tai42-contract` + `tai42-kit` only and never imports the
skeleton.** The provider registers itself as `"accounts-oidc"` in the contract's
module-level accounts registry at import (which also lands it in the identity
registry, since it answers its own session tokens) — there is no import edge to
the skeleton in either direction.

## Ground rules

- **No skeleton import — ever.** The package is contract-facing; the ban is
  enforced by ruff (`flake8-tidy-imports`), so a stray import fails lint:
  ```bash
  grep -rn "tai42_skeleton" src/   # must be empty
  ```
- **Loud errors.** No swallowed exceptions, silent fallbacks, or silent
  truncation. A token-validation or Redis backend error fails closed by
  **raising**; missing `STATE_KEY`/`PUBLIC_BASE_URL` config raises a
  `ValueError` naming the env var at boot; an unreachable issuer or Redis is
  caught loudly by `healthcheck()` at startup.
- **Typed package** (`py.typed`). Pyright runs clean.

## Layout

- `src/tai42_accounts_oidc/provider.py` — the `OidcAccountsProvider`
  (session-token validation, Redis state/SSO-code/session storage) and its
  registration.
- `src/tai42_accounts_oidc/routes.py` — the public `/api/login/oidc/*` authorize +
  callback routes and `/api/login/sso/exchange`.
- `src/tai42_accounts_oidc/oauth.py` — state signing/verification, PKCE, and the
  flow's random tokens.
- `src/tai42_accounts_oidc/presets.py` — the issuer presets (`auth0`, `google`,
  `okta`, `keycloak`, `azure`, `github`) and provider-config resolution.
- `src/tai42_accounts_oidc/settings.py` — the `TAI_ACCOUNTS_OIDC_*` settings and
  provider-list validation.
- `tests/` — behavior against a faked redis seam and a local fake issuer server.

## Naming

PyPI is a flat namespace with no owner in the path, so distributions carry the
`tai42-` prefix. GitHub repositories keep their `tai-` names, because the
`tai42ai` organisation already namespaces them. Import packages follow the
distribution.

| Surface | Form |
| --- | --- |
| Distribution — PyPI, `pip install`, dependency pins | `tai42-<name>` |
| Import package | `tai42_<name>` |
| GitHub repository and sibling checkout directory | `tai-<name>` |

So a dependency is declared as `tai42-<name>` but resolved from `../tai-<name>`
during local development, and both spellings are correct in their own context.

Some surfaces are deliberately neither, and must not be renamed: the `tai` CLI
command (`tai42` is an alias), the Prometheus metric namespace (`tai_tool_*`),
`TAI_*` environment variables, and the `tai-plugin.yml` descriptor filename.

## Dev

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

For local cross-repo work, `make dev` editable-installs the sibling `tai-*`
checkouts this package builds on into the venv. While `[tool.uv.sources]` pins
those siblings to local paths, `uv sync` already installs them editable and
`make dev` changes nothing; once the lock resolves them from the registry,
`uv sync` / `uv run` installs the published builds instead, so re-run
`make dev` afterward to restore the editable links.

Before any commit, run a secret scan over `src/` and `tests/` (e.g.
`detect-secrets scan`).

## License

By contributing you agree your contributions are licensed under Apache-2.0.
