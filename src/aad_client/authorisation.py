"""Provide authorisation via AAD."""

import json
import logging
import os
import sys
from typing import List, Optional

import msal
import requests


_CLIENT_ID_ENV_NAME = 'AAD_CLIENT_ID'
_CLIENT_ID_AZ_CLI_ENV_NAME = 'servicePrincipalId'
_TENANT_ID_ENV_NAME = 'AAD_TENANT_ID'
_TENANT_ID_AZ_CLI_ENV_NAME = 'tenantId'
_CLIENT_SECRET_ENV_NAME = 'AAD_CLIENT_SECRET'
_CLIENT_SECRET_AZ_CLI_ENV_NAME = 'servicePrincipalKey'


logging.basicConfig(level=os.environ.get('LOGLEVEL', 'WARNING'))
logger = logging.getLogger()


class AADAuthentication:
    """AAD Authentication Handler."""

    def __init__(
            self,
            client_id: Optional[str] = None,
            tenant_id: Optional[str] = None,
            client_secret: Optional[str] = None,
            scopes: Optional[List[str]] = None,
            username: Optional[str] = None):
        """Initialise AAD App for device code authentication.

        This can run both as a public app (requiring user login) or as a daemon app (requires a secret).

        Keyword Args:
            client_id (Optional[str]): The client id, defaults to AAD_CLIENT_ID (or servicePrincipalid) if not provided
            tenant_id (Optional[str]): The tenant id, defaults to AAD_TENANT_ID (or tenantId) if not provided
            client_secret (Optional[str]): The client secret, defaults to AAD_CLIENT_SECRET (or servicePrincipalKey) if not provided, signifies a daemon application
            scopes (Optional[List[str]]): The scopes to request as default, can be overridden throught the ``get_token`` method
            username(Optional[str]): The username to use when running as a desktop app
        """
        self.client_id = client_id
        self._username = username
        # We only want to use the spa authentication directly
        if scopes is None:
            scopes = []
        elif isinstance(scopes, str):
            scopes = [scopes]
        self._scopes = scopes
        if client_id is None:
            # We get from the ENV_NAME then the AZ_CLI Env Name
            client_id = os.environ.get(_CLIENT_ID_ENV_NAME, os.environ.get(_CLIENT_ID_AZ_CLI_ENV_NAME, None))
        if tenant_id is None:
            # We get from the ENV_NAME then the AZ_CLI Env Name
            tenant_id = os.environ.get(_TENANT_ID_ENV_NAME, os.environ.get(_TENANT_ID_AZ_CLI_ENV_NAME, None))
        if client_secret is None:
            # We get from the ENV_NAME then the AZ_CLI Env Name
            client_secret = os.environ.get(_CLIENT_SECRET_ENV_NAME, os.environ.get(_CLIENT_SECRET_AZ_CLI_ENV_NAME, None))
        self._authority = f'https://login.microsoftonline.com/{tenant_id}'
        self._daemon = False
        if client_secret:
            self._daemon = True
            # This is running as a daemon application
            self.msal_application = msal.ConfidentialClientApplication(
                client_id,
                authority=self._authority,
                client_credential=client_secret)
        else:
            self.msal_application = msal.PublicClientApplication(
                client_id,
                authority=self._authority)

    def get_tokens(self, scopes=None):
        """Get the token."""
        if scopes is None:
            scopes = self._scopes
        logger.debug(f'Scopes: {scopes}')
        if self._daemon:
            token = self._get_tokens_daemon(scopes)
        else:
            token = self._get_tokens_device_flow(scopes)
        return token

    def _get_tokens_device_flow(self, scopes):
        """Authenticate via device code flow."""
        # https://docs.microsoft.com/en-us/azure/active-directory/develop/scenario-desktop-app-registration
        # From https://docs.microsoft.com/en-us/azure/active-directory/develop/scenario-desktop-acquire-token?tabs=python#command-line-tool-without-a-web-browser
        result = None
        if self._username:
            accounts = self.msal_application.get_accounts(self._username)
            if accounts:
                result = self.msal_application.acquire_token_silent(scopes, account=accounts[0])

        if not result:
            flow = self.msal_application.initiate_device_flow(scopes=self._scopes)
            if "user_code" not in flow:
                raise ValueError(
                    "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

            print(flow["message"])
            sys.stdout.flush()  # Some terminal needs this to ensure the message is shown
            logger.debug(f'flow: {flow}')
            result = self.msal_application.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            # Call a protected API with the access token.
            return result
        else:
            logger.error(f'{result.get("error")}: {result.get("error_description")} (Correlation id: {result.get("correlation_id")}')  # You might need this when reporting a bug.
        return result

    def _get_tokens_daemon(self, scopes):
        """Authenticate via secret flow."""
        # https://docs.microsoft.com/en-us/azure/active-directory/develop/scenario-daemon-overview
        # From https://docs.microsoft.com/en-us/azure/active-directory/develop/scenario-daemon-acquire-token?tabs=dotnet
        result = self.msal_application.acquire_token_silent(scopes=self._scopes, account=None)

        if not result:
            logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
            result = self.msal_application.acquire_token_for_client(scopes=self._scopes)

        if "access_token" in result:
            # Call a protected API with the access token.
            return result
        else:
            logger.error(f'{result.get("error")}: {result.get("error_description")} (Correlation id: {result.get("correlation_id")}')  # You might need this when reporting a bug.

    @property
    def session(self):
        """Get a requests session with authentication."""
        tokens = self.get_tokens()
        access_token = tokens['access_token']
        session = requests.sessions.Session()
        session.headers.update({'Authorization': f'Bearer {access_token}'})
        return session
