"""Client for AAD Authorised Apps."""
from aad_client.authorisation import AADAuthentication  # noqa: F401
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
