"""tai-accounts-oidc: the OIDC/OAuth2 login accounts provider plugin.

Importing this package registers the ``"accounts-oidc"`` provider in the
contract's module-level accounts registry (which also lands it in the identity
registry under the same name, since it answers its own session tokens) — see
:mod:`tai_accounts_oidc.provider`. The public ``/api/login/*`` routes are loaded
separately through the deployment manifest's ``routers_modules``.
"""

from __future__ import annotations

from tai_accounts_oidc.provider import OidcAccountsProvider

__all__ = [
    "OidcAccountsProvider",
]
