"""OAuth 2.0 Client Credentials flow + a small REST client for Salesforce.

Server-to-server: no browser redirect, no refresh token — the agent
re-authenticates from SF_CLIENT_ID/SF_CLIENT_SECRET whenever it needs to.

Salesforce's client_credentials token response does not include an expiry
(token lifetime is governed by the org's session-timeout setting, not
communicated to the client). So instead of tracking an expiry client-side,
the client caches its token and re-authenticates reactively: a 401 on any
request is treated as "the cached token is stale," triggering exactly one
re-auth and retry.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv(".env.local")

API_VERSION = "v61.0"


class SalesforceAuthError(Exception):
    """Raised when the OAuth token request itself fails (bad credentials, etc.)."""


class SalesforceClient:
    def __init__(self, http_client: httpx.Client | None = None):
        self._http = http_client or httpx.Client()
        self._token: str | None = None

    def instance_url(self) -> str:
        return os.environ["SF_INSTANCE_URL"].rstrip("/")

    def _authenticate(self) -> str:
        response = self._http.post(
            f"{self.instance_url()}/services/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.environ["SF_CLIENT_ID"],
                "client_secret": os.environ["SF_CLIENT_SECRET"],
            },
        )
        if response.status_code != 200:
            body = response.json()
            raise SalesforceAuthError(
                f"{body.get('error', 'unknown_error')}: "
                f"{body.get('error_description', response.text)}"
            )
        return response.json()["access_token"]

    def _token_for_request(self, force_refresh: bool = False) -> str:
        if self._token is None or force_refresh:
            self._token = self._authenticate()
        return self._token

    def _send(self, method: str, url: str, **kwargs) -> httpx.Response:
        token = self._token_for_request()
        response = self._http.request(method, url, headers={"Authorization": f"Bearer {token}"}, **kwargs)
        if response.status_code == 401:
            token = self._token_for_request(force_refresh=True)
            response = self._http.request(method, url, headers={"Authorization": f"Bearer {token}"}, **kwargs)
        return response

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """path is relative to /services/data/{API_VERSION}, e.g. '/sobjects/Case'."""
        url = f"{self.instance_url()}/services/data/{API_VERSION}{path}"
        return self._send(method, url, **kwargs)

    def get_userinfo(self) -> dict:
        response = self._send("GET", f"{self.instance_url()}/services/oauth2/userinfo")
        response.raise_for_status()
        return response.json()


def _main() -> None:
    client = SalesforceClient()
    info = client.get_userinfo()
    print(f"[salesforce] authenticated as: {info.get('preferred_username') or info.get('email')}")
    print(f"[salesforce] organization_id: {info.get('organization_id')}")


if __name__ == "__main__":
    _main()
