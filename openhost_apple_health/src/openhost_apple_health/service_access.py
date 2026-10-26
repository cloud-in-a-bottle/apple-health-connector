"""Access control for health-data service calls.

The router reaches this app two ways: as the owner's browser (or a public path), after the router
has done its own auth, and as a service call from another app. Only service calls carry
``X-OpenHost-Consumer-Id``, and the router strips any client-sent copy, so its presence reliably
marks one. A service call may only reach the service-spec endpoints, and only with the spec's
``read`` grant in ``X-OpenHost-Permissions``.
"""

import json
import logging

from litestar import Request, Response
from litestar.connection import ASGIConnection
from litestar.exceptions import NotFoundException
from litestar.handlers import BaseRouteHandler

log = logging.getLogger(__name__)

CONSUMER_ID_HEADER = "X-OpenHost-Consumer-Id"
CONSUMER_NAME_HEADER = "X-OpenHost-Consumer-Name"
PERMISSIONS_HEADER = "X-OpenHost-Permissions"

# Mirrors health_data_service.READ_GRANT in the service spec.
READ_GRANT = "read"

# Set in a route's ``opt`` to mark it as a health-data service-spec endpoint.
SERVICE_ENDPOINT_OPT = "health_data_service_endpoint"
SERVICE_ENDPOINT = {SERVICE_ENDPOINT_OPT: True}


class PermissionRequired(Exception):
    pass


def has_read_grant(permissions_header: str | None) -> bool:
    """Whether the router-supplied permissions include the read grant. A missing or malformed header
    grants nothing."""
    if not permissions_header:
        return False
    try:
        permissions = json.loads(permissions_header)
    except ValueError:
        log.warning("Malformed %s header: %r", PERMISSIONS_HEADER, permissions_header)
        return False
    if not isinstance(permissions, list):
        return False
    return any(isinstance(p, dict) and p.get("grant") == READ_GRANT for p in permissions)


def guard_service_calls(connection: ASGIConnection, route_handler: BaseRouteHandler) -> None:
    """App-wide guard: leaves direct requests alone and gates service calls."""
    if CONSUMER_ID_HEADER not in connection.headers:
        return
    consumer = connection.headers.get(CONSUMER_NAME_HEADER, connection.headers[CONSUMER_ID_HEADER])
    if not route_handler.opt.get(SERVICE_ENDPOINT_OPT):
        # The service is mounted at /api/, which also holds this app's own API (settings with the
        # ingest token, imports). Those are not part of the service.
        log.warning("Refused service call from %s to non-service path %s", consumer, connection.url.path)
        raise NotFoundException()
    if not has_read_grant(connection.headers.get(PERMISSIONS_HEADER)):
        log.info("Refused service call from %s to %s: no %r grant", consumer, connection.url.path, READ_GRANT)
        raise PermissionRequired()


def permission_required_handler(_: Request, __: PermissionRequired) -> Response:
    return Response(
        content={"error": "permission_required", "required_grant": {"grant": READ_GRANT, "scope": "global"}},
        status_code=403,
    )
