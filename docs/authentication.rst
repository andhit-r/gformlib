Authentication
==============

gformlib supports two authentication strategies.

Service Account (recommended for servers)
------------------------------------------

1. Open the `Google Cloud Console <https://console.cloud.google.com/>`_
   and enable the **Google Forms API** and **Google Drive API** for your
   project.
2. Create a **Service Account** and download the JSON key file.
3. Share the Google Drive folder (or individual form) with the service
   account's email address.

.. code-block:: python

    from gformlib import GoogleFormsClient

    client = GoogleFormsClient.from_service_account("service_account.json")

You can also load credentials from a dict (e.g. from an environment
variable or secrets manager):

.. code-block:: python

    import json, os

    info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    client = GoogleFormsClient.from_service_account_info(info)

OAuth 2.0 (desktop / installed apps)
--------------------------------------

1. In the Google Cloud Console create an OAuth 2.0 client of type
   **Desktop app** and download ``client_secrets.json``.
2. On the first run, a browser window opens to grant access.
   The token is cached in ``token.json`` for subsequent runs.

.. code-block:: python

    from gformlib import GoogleFormsClient

    client = GoogleFormsClient.from_oauth_credentials(
        "client_secrets.json",
        token_file="token.json",
    )

Required scopes
---------------

* ``https://www.googleapis.com/auth/forms.body`` – create and edit forms.
* ``https://www.googleapis.com/auth/drive.file`` – required for file-upload
  questions and ``delete_form``.
