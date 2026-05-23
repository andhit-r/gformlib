"""Main client for the Google Forms API.

This module exposes :class:`GoogleFormsClient`, the primary public interface
of the ``gformlib`` library.  The client handles authentication, delegates
request-body construction to :class:`~gformlib.builder.FormBuilder`, and
wraps the raw Google API responses in typed :class:`~gformlib.models.FormInfo`
objects.

Supported authentication strategies
-------------------------------------
1. **Service Account** (server-to-server) – :meth:`GoogleFormsClient.from_service_account`
2. **OAuth 2.0 installed app** – :meth:`GoogleFormsClient.from_oauth_credentials`
3. **Pre-built credentials** – pass any ``google.oauth2`` credentials object
   directly to the constructor.

Required Google API scopes
---------------------------
* ``https://www.googleapis.com/auth/forms.body`` – create and modify forms
* ``https://www.googleapis.com/auth/drive.file`` – required for file-upload questions

Example::

    from gformlib import GoogleFormsClient

    client = GoogleFormsClient.from_service_account("service_account.json")
    info = client.create_form(
        {
            "title": "Quick Survey",
            "description": "Tell us what you think.",
            "questions": [
                {"title": "Your name", "type": "short_answer", "required": True},
                {
                    "title": "Rating",
                    "type": "scale",
                    "low": 1,
                    "high": 5,
                    "low_label": "Poor",
                    "high_label": "Excellent",
                },
            ],
        }
    )
    print(info.responder_uri)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Union

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .builder import FormBuilder
from .exceptions import APIError, AuthenticationError, FormCreationError, FormUpdateError
from .models import FormConfig, FormInfo, UpdateFormConfig
from .utils import parse_form_config, parse_update_config

logger = logging.getLogger(__name__)

#: Default OAuth scopes required by the Google Forms API.
DEFAULT_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleFormsClient:
    """High-level client for creating and managing Google Forms.

    Do **not** instantiate this class directly with the constructor unless
    you already have a ``google.oauth2`` credentials object.  Use one of
    the class-method factories instead:

    * :meth:`from_service_account` – recommended for server-side code.
    * :meth:`from_oauth_credentials` – for installed / desktop apps.

    Args:
        credentials: Any ``google.oauth2`` credentials object that has
            been authorised for the required scopes.
        scopes: OAuth scopes to request.  Defaults to
            :data:`DEFAULT_SCOPES`.

    Raises:
        AuthenticationError: If the credentials object is ``None`` or
            invalid.

    Example::

        from google.oauth2.service_account import Credentials
        from gformlib import GoogleFormsClient

        creds = Credentials.from_service_account_file("sa.json", scopes=[...])
        client = GoogleFormsClient(credentials=creds)
    """

    def __init__(
        self,
        credentials: Any,
        scopes: Optional[List[str]] = None,
    ) -> None:
        if credentials is None:
            raise AuthenticationError("credentials must not be None.")
        self._credentials = credentials
        self._scopes = scopes or DEFAULT_SCOPES
        self._service = build("forms", "v1", credentials=self._credentials)

    # ──────────────────────────────────────────────────────────────────────
    # Factories
    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    def from_service_account(
        cls,
        service_account_file: Union[str, os.PathLike[str]],
        scopes: Optional[List[str]] = None,
        subject: Optional[str] = None,
    ) -> "GoogleFormsClient":
        """Create a client authenticated as a Google Service Account.

        This is the recommended approach for server-side applications that
        do not have a logged-in user context.

        Args:
            service_account_file: Path to the service account JSON key file
                downloaded from the Google Cloud Console.
            scopes: OAuth scopes to request.  Defaults to
                :data:`DEFAULT_SCOPES`.
            subject: The email address of the user account to impersonate
                (requires Domain-Wide Delegation to be configured).

        Returns:
            An authenticated :class:`GoogleFormsClient`.

        Raises:
            AuthenticationError: If the key file cannot be read or the
                credentials are invalid.
            FileNotFoundError: If *service_account_file* does not exist.

        Example::

            client = GoogleFormsClient.from_service_account(
                "path/to/service_account.json"
            )
        """
        _scopes = scopes or DEFAULT_SCOPES
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(service_account_file),
                scopes=_scopes,
                subject=subject,
            )
        except Exception as exc:
            raise AuthenticationError(
                f"Failed to load service account credentials from "
                f"'{service_account_file}': {exc}"
            ) from exc
        return cls(credentials=credentials, scopes=_scopes)

    @classmethod
    def from_service_account_info(
        cls,
        info: Dict[str, Any],
        scopes: Optional[List[str]] = None,
        subject: Optional[str] = None,
    ) -> "GoogleFormsClient":
        """Create a client from a service account info dict.

        Useful when credentials are stored in environment variables or a
        secrets manager rather than on the file system.

        Args:
            info: Service account info dict (the parsed contents of a
                service account JSON key file).
            scopes: OAuth scopes to request.  Defaults to
                :data:`DEFAULT_SCOPES`.
            subject: Email address of the user to impersonate (requires
                Domain-Wide Delegation).

        Returns:
            An authenticated :class:`GoogleFormsClient`.

        Raises:
            AuthenticationError: If *info* is invalid.

        Example::

            import json, os
            info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
            client = GoogleFormsClient.from_service_account_info(info)
        """
        _scopes = scopes or DEFAULT_SCOPES
        try:
            credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=_scopes,
                subject=subject,
            )
        except Exception as exc:
            raise AuthenticationError(
                f"Failed to create service account credentials from info dict: {exc}"
            ) from exc
        return cls(credentials=credentials, scopes=_scopes)

    @classmethod
    def from_oauth_credentials(
        cls,
        client_secrets_file: Union[str, os.PathLike[str]],
        token_file: Optional[Union[str, os.PathLike[str]]] = None,
        scopes: Optional[List[str]] = None,
    ) -> "GoogleFormsClient":
        """Create a client using the OAuth 2.0 installed-app flow.

        On the first run the user is prompted to grant access in their
        browser.  The resulting token is saved to *token_file* so subsequent
        runs are non-interactive.

        Args:
            client_secrets_file: Path to the ``client_secrets.json`` file
                downloaded from the Google Cloud Console (OAuth 2.0 client
                ID of type *Desktop app*).
            token_file: Path where the OAuth token will be cached.
                Defaults to ``"token.json"`` in the current directory.
            scopes: OAuth scopes to request.  Defaults to
                :data:`DEFAULT_SCOPES`.

        Returns:
            An authenticated :class:`GoogleFormsClient`.

        Raises:
            AuthenticationError: If the OAuth flow fails.
            FileNotFoundError: If *client_secrets_file* does not exist.

        Example::

            client = GoogleFormsClient.from_oauth_credentials(
                "client_secrets.json",
                token_file="my_token.json",
            )
        """
        _scopes = scopes or DEFAULT_SCOPES
        _token_path = str(token_file) if token_file else "token.json"

        credentials: Optional[Credentials] = None
        if os.path.exists(_token_path):
            try:
                credentials = Credentials.from_authorized_user_file(_token_path, _scopes)
            except Exception:
                logger.debug("Token file '%s' could not be loaded; re-authorising.", _token_path)
                credentials = None

        if not credentials or not credentials.valid:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_file), _scopes)
                credentials = flow.run_local_server(port=0)
            except Exception as exc:
                raise AuthenticationError(f"OAuth flow failed: {exc}") from exc
            try:
                with open(_token_path, "w") as token_fh:
                    token_fh.write(credentials.to_json())
                logger.debug("OAuth token saved to '%s'.", _token_path)
            except OSError as exc:
                logger.warning("Could not save token to '%s': %s", _token_path, exc)

        return cls(credentials=credentials, scopes=_scopes)

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def create_form(
        self,
        config: Union[Dict[str, Any], FormConfig],
    ) -> FormInfo:
        """Create a new Google Form from a configuration dict or
        :class:`~gformlib.models.FormConfig`.

        This method:

        1. Validates *config* (if it is a dict) with
           :func:`~gformlib.utils.parse_form_config`.
        2. Calls ``forms().create()`` to create the bare form skeleton.
        3. Calls ``forms().batchUpdate()`` to add questions and description.

        Args:
            config: Either a raw configuration dict (see :ref:`quickstart`)
                or a pre-built :class:`~gformlib.models.FormConfig` object.

        Returns:
            A :class:`~gformlib.models.FormInfo` with the form's ID,
            responder URL, and other metadata.

        Raises:
            InvalidConfigError: If *config* fails validation.
            FormCreationError: If the ``forms().create()`` call fails.
            FormUpdateError: If the ``forms().batchUpdate()`` call fails.
            APIError: On unexpected HTTP errors from the Forms API.

        Example::

            info = client.create_form(
                {
                    "title": "My Survey",
                    "questions": [
                        {"title": "Name", "type": "short_answer", "required": True},
                    ],
                }
            )
            print(info.responder_uri)
        """
        if isinstance(config, dict):
            form_config: FormConfig = parse_form_config(config)
        else:
            form_config = config

        builder = FormBuilder(form_config)

        # Step 1 – create the form shell
        create_body = builder.build_create_body()
        logger.debug("Creating form with body: %s", create_body)
        try:
            form_response = self._service.forms().create(body=create_body).execute()
        except HttpError as exc:
            raise FormCreationError(
                f"Failed to create form '{form_config.title}': {exc}",
                config=create_body,
            ) from exc
        except Exception as exc:
            raise FormCreationError(
                f"Unexpected error creating form: {exc}",
                config=create_body,
            ) from exc

        form_id: str = form_response["formId"]
        logger.info("Form created with ID '%s'.", form_id)

        # Step 2 – add questions + description via batchUpdate
        batch_body = builder.build_batch_update_body()
        if batch_body.get("requests"):
            logger.debug(
                "Updating form '%s' with %d request(s).", form_id, len(batch_body["requests"])
            )
            try:
                self._service.forms().batchUpdate(formId=form_id, body=batch_body).execute()
            except HttpError as exc:
                raise FormUpdateError(
                    f"Failed to add questions to form '{form_id}': {exc}",
                    form_id=form_id,
                ) from exc
            except Exception as exc:
                raise FormUpdateError(
                    f"Unexpected error updating form '{form_id}': {exc}",
                    form_id=form_id,
                ) from exc

        return self._parse_form_info(form_response)

    def update_form(
        self,
        form_id: str,
        config: Union[Dict[str, Any], UpdateFormConfig],
    ) -> FormInfo:
        """Update an existing Google Form.

        Modifies the title, description, and/or appends new questions to an
        existing form identified by *form_id*.  Only the fields explicitly set
        in *config* are changed; everything else is left untouched.

        This method:

        1. Validates *config* (if it is a dict) with
           :func:`~gformlib.utils.parse_update_config`.
        2. If new questions are being added, calls ``forms().get()`` first to
           determine the current item count so that questions are appended at
           the correct position.
        3. Calls ``forms().batchUpdate()`` with the generated request list.
        4. Returns a :class:`~gformlib.models.FormInfo` reflecting the
           updated form state.

        Args:
            form_id: The ID of the form to update.
            config: Either a raw update configuration dict or a pre-built
                :class:`~gformlib.models.UpdateFormConfig` object.

                Recognised dict keys:

                * ``"title"`` *(str)* – new form title.
                * ``"description"`` *(str)* – new form description.
                * ``"add_questions"`` *(list)* – question dicts to append.

        Returns:
            A :class:`~gformlib.models.FormInfo` with the updated metadata.

        Raises:
            InvalidConfigError: If *config* fails validation.
            APIError: If the ``forms().get()`` call to fetch the current
                form state fails.
            FormUpdateError: If the ``forms().batchUpdate()`` call fails.

        Example::

            info = client.update_form(
                "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
                {
                    "title": "Revised Survey",
                    "add_questions": [
                        {"title": "Any comments?", "type": "paragraph"},
                    ],
                },
            )
            print(info.title)
        """
        if isinstance(config, dict):
            update_config: UpdateFormConfig = parse_update_config(config)
        else:
            update_config = config

        # If questions are being added, get the current item count so that
        # new questions are appended after existing ones.
        start_index: int = 0
        if update_config.add_questions:
            try:
                current_form = self._service.forms().get(formId=form_id).execute()
                start_index = len(current_form.get("items", []))
            except HttpError as exc:
                raise APIError(
                    f"Failed to fetch form '{form_id}' before update: {exc}",
                    status_code=exc.status_code,
                ) from exc

        batch_body = FormBuilder.build_update_body(update_config, start_index=start_index)

        if not batch_body.get("requests"):
            # Nothing to update – just return the current form state.
            logger.debug("update_form called with no changes for form '%s'.", form_id)
            try:
                form_response = self._service.forms().get(formId=form_id).execute()
            except HttpError as exc:
                raise APIError(
                    f"Failed to get form '{form_id}': {exc}",
                    status_code=exc.status_code,
                ) from exc
            return self._parse_form_info(form_response)

        logger.debug(
            "Updating form '%s' with %d request(s).", form_id, len(batch_body["requests"])
        )
        try:
            update_response = (
                self._service.forms().batchUpdate(formId=form_id, body=batch_body).execute()
            )
        except HttpError as exc:
            raise FormUpdateError(
                f"Failed to update form '{form_id}': {exc}",
                form_id=form_id,
            ) from exc
        except Exception as exc:
            raise FormUpdateError(
                f"Unexpected error updating form '{form_id}': {exc}",
                form_id=form_id,
            ) from exc

        # batchUpdate returns {"form": <FormResponse>, "replies": [...]}
        form_response = update_response.get("form") or {}
        if not form_response.get("formId"):
            # Fall back to an explicit get when the response is incomplete.
            try:
                form_response = self._service.forms().get(formId=form_id).execute()
            except HttpError as exc:
                raise APIError(
                    f"Failed to get form '{form_id}' after update: {exc}",
                    status_code=exc.status_code,
                ) from exc

        logger.info("Form '%s' updated successfully.", form_id)
        return self._parse_form_info(form_response)

    def get_form(self, form_id: str) -> Dict[str, Any]:
        """Retrieve the full metadata of an existing form.

        Args:
            form_id: The ID of the form to retrieve.

        Returns:
            The raw JSON response dict from the ``forms().get()`` call.

        Raises:
            APIError: If the form is not found or the API returns an error.

        Example::

            data = client.get_form("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms")
        """
        try:
            return self._service.forms().get(formId=form_id).execute()
        except HttpError as exc:
            raise APIError(
                f"Failed to get form '{form_id}': {exc}",
                status_code=exc.status_code,
            ) from exc

    def list_responses(
        self,
        form_id: str,
        page_size: int = 100,
        filter_str: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve all responses submitted to a form.

        Automatically handles pagination via the ``nextPageToken`` returned
        by the API.

        Args:
            form_id: The ID of the form to retrieve responses for.
            page_size: Maximum number of responses per API page.
                Defaults to ``100`` (the API maximum).
            filter_str: Optional filter string in the format accepted by
                the Forms API (e.g. ``"timestamp > 2024-01-01T00:00:00Z"``).

        Returns:
            A list of raw response dicts from the API.

        Raises:
            APIError: If the API call fails.

        Example::

            responses = client.list_responses(form_id)
            for r in responses:
                print(r["responseId"])
        """
        results: List[Dict[str, Any]] = []
        page_token: Optional[str] = None

        while True:
            kwargs: Dict[str, Any] = {
                "formId": form_id,
                "pageSize": page_size,
            }
            if page_token:
                kwargs["pageToken"] = page_token
            if filter_str:
                kwargs["filter"] = filter_str

            try:
                resp = self._service.forms().responses().list(**kwargs).execute()
            except HttpError as exc:
                raise APIError(
                    f"Failed to list responses for form '{form_id}': {exc}",
                    status_code=exc.status_code,
                ) from exc

            results.extend(resp.get("responses", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return results

    def delete_form(self, form_id: str) -> None:
        """Delete a form by moving it to the Google Drive trash.

        The Google Forms API does not expose a direct ``delete`` endpoint;
        this method calls the Drive API to trash the backing document.

        Args:
            form_id: The ID of the form (same as the Drive file ID).

        Raises:
            APIError: If the Drive API call fails.

        Note:
            This requires the ``https://www.googleapis.com/auth/drive.file``
            scope to be included in the credentials.

        Example::

            client.delete_form("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms")
        """
        try:
            drive_service = build("drive", "v3", credentials=self._credentials)
            drive_service.files().trash(fileId=form_id).execute()
            logger.info("Form '%s' moved to trash.", form_id)
        except HttpError as exc:
            raise APIError(
                f"Failed to delete form '{form_id}': {exc}",
                status_code=exc.status_code,
            ) from exc

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_form_info(response: Dict[str, Any]) -> FormInfo:
        """Convert a raw ``forms().create()`` response into :class:`~gformlib.models.FormInfo`.

        Args:
            response: Raw JSON dict returned by the Google Forms API.

        Returns:
            A :class:`~gformlib.models.FormInfo` instance.
        """
        info = response.get("info", {})
        linked_sheet_id: Optional[str] = None
        if response.get("linkedSheetId"):
            linked_sheet_id = response["linkedSheetId"]

        return FormInfo(
            form_id=response["formId"],
            title=info.get("title", ""),
            document_title=info.get("documentTitle", ""),
            responder_uri=response.get("responderUri", ""),
            linked_sheet_id=linked_sheet_id,
            revision_id=response.get("revisionId"),
            raw=response,
        )
