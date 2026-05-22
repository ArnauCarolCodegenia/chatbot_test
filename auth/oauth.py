"""
OAuth 2.0 authentication helpers for ADK tools.

ADK supports attaching auth schemes to OpenAPI toolsets and RestApiTools so the
agent can call authenticated APIs on behalf of the user.

Supported scheme types:
  - OAuth2 (Authorization Code flow)
  - APIKey (header / query param)
  - HTTPBearer (Bearer token)
  - OpenIdConnectWithConfig (OIDC)

SETUP:
  1. Create OAuth 2.0 credentials in GCP Console:
       APIs & Services → Credentials → Create OAuth client ID
       Application type: Web application
       Authorised redirect URI: http://localhost:8080/oauth2callback (dev)

  2. Set in .env:
       OAUTH_CLIENT_ID=your-client-id
       OAUTH_CLIENT_SECRET=your-client-secret
       OAUTH_REDIRECT_URI=http://localhost:8080/oauth2callback

  3. Use build_authenticated_toolset() to wrap your OpenAPI spec with OAuth.

NOTE: For production, store tokens in DatabaseSessionService, not in memory.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def build_oauth_scheme(
    authorization_url: str,
    token_url: str,
    scopes: dict[str, str] | None = None,
):
    """Build an OAuth2 scheme for use with OpenAPIToolset."""
    from google.adk.auth import OAuth2

    return OAuth2(
        authorizationUrl=authorization_url,
        tokenUrl=token_url,
        scopes=scopes or {},
    )


def build_oauth_credential():
    """Build OAuth credentials from environment variables."""
    from google.adk.auth import AuthCredential, AuthCredentialTypes, OAuth2Auth

    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET must be set in .env")

    return AuthCredential(
        auth_type=AuthCredentialTypes.OAUTH2,
        oauth2=OAuth2Auth(
            client_id=client_id,
            client_secret=client_secret,
        ),
    )


def build_authenticated_toolset(openapi_spec: dict, authorization_url: str, token_url: str, scopes: dict | None = None):
    """
    Wrap an OpenAPI spec dict with OAuth2 authentication.

    Args:
        openapi_spec:      Parsed OpenAPI 3.x spec as a Python dict.
        authorization_url: OAuth provider's authorization endpoint.
        token_url:         OAuth provider's token endpoint.
        scopes:            Dict of scope -> description (e.g. {"read:data": "Read data"}).

    Returns:
        OpenAPIToolset ready to add to an agent's tools=[].
    """
    from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

    scheme = build_oauth_scheme(authorization_url, token_url, scopes)
    credential = build_oauth_credential()

    return OpenAPIToolset(
        spec_dict=openapi_spec,
        auth_scheme=scheme,
        auth_credential=credential,
    )


"""
API Key authentication example — uncomment as needed:

def build_api_key_tool(base_url: str, api_key_header: str = "X-API-Key"):
    from google.adk.tools import RestApiTool
    from google.adk.auth import APIKey, AuthCredential, AuthCredentialTypes

    scheme = APIKey(name=api_key_header, in_="header")
    credential = AuthCredential(
        auth_type=AuthCredentialTypes.API_KEY,
        api_key=os.getenv("EXTERNAL_API_KEY"),
    )
    # Use with individual RestApiTool instances
    return scheme, credential


def build_bearer_token_scheme(token_env_var: str = "BEARER_TOKEN"):
    from google.adk.auth import HTTPBearer, AuthCredential, AuthCredentialTypes

    scheme = HTTPBearer()
    credential = AuthCredential(
        auth_type=AuthCredentialTypes.HTTP,
        http=HttpAuth(
            scheme="bearer",
            credentials=HttpCredentials(token=os.getenv(token_env_var, "")),
        ),
    )
    return scheme, credential
"""
