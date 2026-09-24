"""Client interface for communicating with homelabd."""

from homelabctl.client.backend_client import (
    BackendClient,
    request_sync,
)

__all__ = [
    "BackendClient",
    "request_sync",
]
