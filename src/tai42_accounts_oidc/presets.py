"""Provider presets — defaults, never magic.

A preset fills a provider row's ``display.label`` and, where an issuer is
globally fixed (``google``), the issuer. It never bundles a brand icon (label
text only). The per-tenant presets (``auth0``/``okta``/``keycloak``/``azure``)
leave the issuer as REQUIRED operator config — a row that names one without an
issuer raises at settings load, naming the field.

``github`` is the odd one out: it selects the plain-OAuth2 code path — no OIDC
discovery, no id_token. Its fixed endpoints and the ``GET /user`` identity call
are module constants here so the OIDC path never branches on GitHub beyond the
one dispatch on :attr:`ResolvedProvider.kind`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import SecretStr

from tai42_accounts_oidc.settings import OidcProviderConfig

# GitHub's plain-OAuth2 endpoints (no discovery document exists). Module
# constants so they are the single source of truth; the login flow references
# these by name.
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"

# GitHub OAuth maps identity by the numeric account ``id`` by default (``sub``
# has no meaning outside OIDC), so a GitHub row that left ``claim`` at its
# field default resolves to this instead.
_GITHUB_DEFAULT_CLAIM = "id"


@dataclass(frozen=True)
class _Preset:
    label: str
    issuer: str | None  # a globally-fixed issuer, or None when it is per-tenant operator config


# The OIDC presets. ``google`` fixes its issuer; the rest are per-tenant and
# require the operator to supply one.
_OIDC_PRESETS: dict[str, _Preset] = {
    "auth0": _Preset(label="Continue with Auth0", issuer=None),
    "google": _Preset(label="Continue with Google", issuer="https://accounts.google.com"),
    "okta": _Preset(label="Continue with Okta", issuer=None),
    "keycloak": _Preset(label="Continue with Keycloak", issuer=None),
    "azure": _Preset(label="Continue with Microsoft", issuer=None),
}

_GITHUB_LABEL = "Continue with GitHub"


@dataclass(frozen=True)
class ResolvedProvider:
    """A provider row with its preset applied — the runtime login-flow shape."""

    name: str
    kind: Literal["oidc", "github"]
    client_id: str
    client_secret: SecretStr
    scopes: tuple[str, ...]
    claim: str
    label: str
    icon: str | None
    # The OIDC issuer (discovery base). ``None`` exactly when ``kind == "github"``.
    issuer: str | None


def resolve_provider(config: OidcProviderConfig) -> ResolvedProvider:
    """Apply ``config``'s preset and return the runtime :class:`ResolvedProvider`.

    Raises ``ValueError`` — surfaced at settings load — when a preset that needs a
    per-tenant issuer (or a raw row with no preset) is missing one.
    """
    if config.preset == "github":
        return _resolve_github(config)
    return _resolve_oidc(config)


def _resolve_github(config: OidcProviderConfig) -> ResolvedProvider:
    claim = _GITHUB_DEFAULT_CLAIM if config.claim == "sub" else config.claim
    return ResolvedProvider(
        name=config.name,
        kind="github",
        client_id=config.client_id,
        client_secret=config.client_secret,
        scopes=tuple(config.scopes),
        claim=claim,
        label=_label(config, _GITHUB_LABEL),
        icon=config.display.icon,
        issuer=None,
    )


def _resolve_oidc(config: OidcProviderConfig) -> ResolvedProvider:
    preset = _OIDC_PRESETS.get(config.preset) if config.preset is not None else None
    # A preset with a globally-fixed issuer (google) wins; otherwise the operator
    # must supply one (per-tenant preset, or a raw row with no preset at all).
    issuer = preset.issuer if preset is not None and preset.issuer is not None else config.issuer
    if issuer is None:
        raise ValueError(
            f"provider {config.name!r} has no issuer: "
            f"{'preset ' + config.preset + ' is per-tenant, so' if config.preset else 'a raw provider row'} "
            "requires an explicit 'issuer'"
        )
    preset_label = preset.label if preset is not None else None
    return ResolvedProvider(
        name=config.name,
        kind="oidc",
        client_id=config.client_id,
        client_secret=config.client_secret,
        scopes=tuple(config.scopes),
        claim=config.claim,
        label=_label(config, preset_label),
        icon=config.display.icon,
        issuer=issuer,
    )


def _label(config: OidcProviderConfig, preset_label: str | None) -> str:
    """The button label: an explicit operator label wins, else the preset's, else
    a generic fallback (a raw provider with no preset and no label)."""
    if config.display.label:
        return config.display.label
    if preset_label is not None:
        return preset_label
    return f"Sign in with {config.name}"
