import pytest

from agent.salesforce_client import SalesforceAuthError, SalesforceClient


class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text or str(json_data)

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeHttpClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return self._responses.pop(0)

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self._responses.pop(0)


@pytest.fixture(autouse=True)
def sf_env(monkeypatch):
    monkeypatch.setenv("SF_INSTANCE_URL", "https://example-org.my.salesforce.com")
    monkeypatch.setenv("SF_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SF_CLIENT_SECRET", "test-client-secret")


def test_token_is_fetched_once_and_cached_across_requests():
    http = FakeHttpClient(
        [
            FakeResponse(200, {"access_token": "token-a"}),
            FakeResponse(200, {"records": []}),
            FakeResponse(200, {"records": []}),
        ]
    )
    client = SalesforceClient(http_client=http)

    client.request("GET", "/sobjects/Case")
    client.request("GET", "/sobjects/Case")

    post_calls = [call for call in http.calls if call[0] == "POST"]
    assert len(post_calls) == 1


def test_bad_credentials_raise_salesforce_auth_error_with_details():
    http = FakeHttpClient(
        [
            FakeResponse(
                400,
                {"error": "invalid_client", "error_description": "client identifier invalid"},
            )
        ]
    )
    client = SalesforceClient(http_client=http)

    with pytest.raises(SalesforceAuthError) as exc_info:
        client.request("GET", "/sobjects/Case")

    assert "invalid_client" in str(exc_info.value)
    assert "client identifier invalid" in str(exc_info.value)


def test_401_triggers_one_reauth_and_retry_with_new_token():
    http = FakeHttpClient(
        [
            FakeResponse(200, {"access_token": "token-a"}),
            FakeResponse(401, {"error": "INVALID_SESSION_ID"}),
            FakeResponse(200, {"access_token": "token-b"}),
            FakeResponse(200, {"records": []}),
        ]
    )
    client = SalesforceClient(http_client=http)

    response = client.request("GET", "/sobjects/Case")

    assert response.status_code == 200
    post_calls = [call for call in http.calls if call[0] == "POST"]
    assert len(post_calls) == 2  # initial auth + re-auth after the 401
    retry_call = http.calls[-1]
    assert retry_call[2]["headers"]["Authorization"] == "Bearer token-b"


def test_get_userinfo_returns_parsed_identity():
    http = FakeHttpClient(
        [
            FakeResponse(200, {"access_token": "token-a"}),
            FakeResponse(200, {"preferred_username": "agent@example.org", "organization_id": "00Dxx"}),
        ]
    )
    client = SalesforceClient(http_client=http)

    info = client.get_userinfo()

    assert info["preferred_username"] == "agent@example.org"
    assert info["organization_id"] == "00Dxx"
