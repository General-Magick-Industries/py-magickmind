"""Resource clients for API endpoints."""

from .base import BaseResource

# TODO: Add V1Resources, V2Resources when resources are implemented
# See docs/contributing/resource_implementation_guide/ for reference
#
# Example:
# from .v1.chat import ChatResourceV1
# from .v2.chat import ChatResourceV2
#
# class V1Resources:
#     """Container for all v1 API resources."""
#     def __init__(self, http_client):
#         self.chat = ChatResourceV1(http_client)
#
# class V2Resources:
#     """Container for all v2 API resources."""
#     def __init__(self, http_client):
#         self.chat = ChatResourceV2(http_client)

__all__ = ["BaseResource"]
