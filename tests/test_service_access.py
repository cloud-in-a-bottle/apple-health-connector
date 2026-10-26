import json

import pytest
from litestar import Litestar, get
from litestar.testing import TestClient

from openhost_apple_health.service_access import (
    SERVICE_ENDPOINT,
    PermissionRequired,
    guard_service_calls,
    permission_required_handler,
)


@get("/api/v1/metrics", opt=SERVICE_ENDPOINT)
async def service_route() -> dict:
    return {"metrics": []}


@get("/api/v1/settings")
async def private_route() -> dict:
    return {"api_key": "secret"}


@pytest.fixture
def client():
    app = Litestar(
        route_handlers=[service_route, private_route],
        guards=[guard_service_calls],
        exception_handlers={PermissionRequired: permission_required_handler},
    )
    with TestClient(app=app) as c:
        yield c


def _service_call(permissions: object) -> dict[str, str]:
    return {
        "X-OpenHost-Consumer-Id": "consumer-id",
        "X-OpenHost-Consumer-Name": "consumer",
        "X-OpenHost-Permissions": json.dumps(permissions),
    }


def test_direct_requests_are_not_gated(client):
    # No consumer headers: the router has already applied owner auth / public paths.
    assert client.get("/api/v1/metrics").status_code == 200
    assert client.get("/api/v1/settings").status_code == 200


def test_service_call_with_read_grant(client):
    r = client.get("/api/v1/metrics", headers=_service_call([{"grant": "read", "scope": "global"}]))
    assert r.status_code == 200
    assert r.json() == {"metrics": []}


@pytest.mark.parametrize(
    "permissions",
    [[], [{"grant": "full_access", "scope": "global"}], [{"grant": {"read": True}, "scope": "global"}], {"grant": "read"}],
    ids=["none", "other-grant", "object-grant", "not-a-list"],
)
def test_service_call_without_read_grant(client, permissions):
    r = client.get("/api/v1/metrics", headers=_service_call(permissions))
    assert r.status_code == 403
    assert r.json() == {"error": "permission_required", "required_grant": {"grant": "read", "scope": "global"}}


def test_service_call_with_malformed_permissions(client):
    headers = {**_service_call([]), "X-OpenHost-Permissions": "not json"}
    assert client.get("/api/v1/metrics", headers=headers).status_code == 403


def test_service_call_cannot_reach_non_service_route(client):
    r = client.get("/api/v1/settings", headers=_service_call([{"grant": "read", "scope": "global"}]))
    assert r.status_code == 404
    assert "secret" not in r.text
