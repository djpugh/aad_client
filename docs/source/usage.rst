Using aad_client
****************

``aad_client`` requires an Azure Active Directory App Registration (from the Azure Active Directory you want
the application to authenticate against), and these parameters should then be set in environment variables
(or a ``.env`` environment file) within the environment that fastapi is being served from.

.. _config-aad-appreg:

Configuring the Azure Active Directory App Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are several parts of the App Registration to Configure, and this depends if you want to run as a
`Daemon application <https://docs.microsoft.com/en-us/azure/active-directory/develop/scenario-daemon-app-registration>`_
or an `Interactive application <https://docs.microsoft.com/en-us/azure/active-directory/develop/scenario-desktop-app-registration>`_.
The daemon application will need Azure Active Directory admin credentials to approve.

Once your app registration is configured, you need to configure your local environment, this can be done either via the authorisation object
or the environmnet variables.

The device code flow seems to need the msal redirect URI enabled (``msal<client-id>://auth``).

Configuring via environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are several key parameters:

 - ``AAD_CLIENT_ID``: The Azure Active Directory App Registration Client ID
 - ``AAD_TENANT_ID``: The Azure Active Directory App Registration Client ID

The ``AAD_CLIENT_SECRET`` parameter is needed if your application is a daemon client (Generated
from the certificates and secrets section of the app registration) (see above).


Using within python
~~~~~~~~~~~~~~~~~~~


.. autoclass:: aad_client.AADAuthentication
    :members: