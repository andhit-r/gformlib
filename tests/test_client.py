"""Unit tests for :mod:`gformlib.client`."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, call, patch

import pytest
from googleapiclient.errors import HttpError

from gformlib.client import DEFAULT_SCOPES, GoogleFormsClient
from gformlib.exceptions import (
    APIError,
    AuthenticationError,
    FormCreationError,
    FormUpdateError,
    InvalidConfigError,
)
from gformlib.models import FormInfo


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_http_error(status: int = 403) -> HttpError:
    """Create a minimal HttpError for testing."""
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=b"error")


# ─────────────────────────────────────────────────────────────────────────────
# Construction / factories
# ─────────────────────────────────────────────────────────────────────────────


class TestGoogleFormsClientConstruction:
    """Tests for constructing a :class:`GoogleFormsClient`."""

    def test_none_credentials_raises(self) -> None:
        """Passing None as credentials raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            with patch("gformlib.client.build"):
                GoogleFormsClient(credentials=None)

    def test_valid_credentials_succeed(self, mock_credentials, mock_service) -> None:
        """Valid credentials construct the client without error."""
        with patch("gformlib.client.build", return_value=mock_service):
            c = GoogleFormsClient(credentials=mock_credentials)
        assert c is not None

    def test_default_scopes(self, mock_credentials, mock_service) -> None:
        """Default scopes match DEFAULT_SCOPES."""
        with patch("gformlib.client.build", return_value=mock_service):
            c = GoogleFormsClient(credentials=mock_credentials)
        assert c._scopes == DEFAULT_SCOPES

    def test_custom_scopes(self, mock_credentials, mock_service) -> None:
        """Custom scopes are stored."""
        custom = ["https://www.googleapis.com/auth/forms.body"]
        with patch("gformlib.client.build", return_value=mock_service):
            c = GoogleFormsClient(credentials=mock_credentials, scopes=custom)
        assert c._scopes == custom


class TestFromServiceAccount:
    """Tests for :meth:`GoogleFormsClient.from_service_account`."""

    def test_missing_file_raises(self) -> None:
        """A non-existent key file raises AuthenticationError."""
        with pytest.raises(AuthenticationError, match="Failed to load"):
            GoogleFormsClient.from_service_account("/nonexistent/sa.json")

    def test_successful_load(self, tmp_path, mock_service) -> None:
        """A valid key file produces an authenticated client."""
        key_file = tmp_path / "sa.json"
        key_file.write_text("{}")  # content doesn't matter – we mock

        mock_creds = MagicMock()
        with (
            patch(
                "gformlib.client.service_account.Credentials.from_service_account_file",
                return_value=mock_creds,
            ),
            patch("gformlib.client.build", return_value=mock_service),
        ):
            client = GoogleFormsClient.from_service_account(str(key_file))
        assert isinstance(client, GoogleFormsClient)


class TestFromServiceAccountInfo:
    """Tests for :meth:`GoogleFormsClient.from_service_account_info`."""

    def test_successful_load(self, mock_service) -> None:
        """A valid info dict produces an authenticated client."""
        mock_creds = MagicMock()
        with (
            patch(
                "gformlib.client.service_account.Credentials.from_service_account_info",
                return_value=mock_creds,
            ),
            patch("gformlib.client.build", return_value=mock_service),
        ):
            client = GoogleFormsClient.from_service_account_info(
                {"type": "service_account"}
            )
        assert isinstance(client, GoogleFormsClient)

    def test_invalid_info_raises(self) -> None:
        """An invalid info dict raises AuthenticationError."""
        with pytest.raises(AuthenticationError, match="Failed to create"):
            with patch(
                "gformlib.client.service_account.Credentials.from_service_account_info",
                side_effect=ValueError("bad"),
            ):
                GoogleFormsClient.from_service_account_info({})


# ─────────────────────────────────────────────────────────────────────────────
# create_form
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateForm:
    """Tests for :meth:`GoogleFormsClient.create_form`."""

    def _setup_service(
        self, mock_service, create_response, batch_response=None
    ) -> None:
        """Wire the mock service to return the given responses."""
        create_mock = MagicMock()
        create_mock.execute.return_value = create_response

        batch_mock = MagicMock()
        batch_mock.execute.return_value = batch_response or {}

        mock_service.forms.return_value.create.return_value = create_mock
        mock_service.forms.return_value.batchUpdate.return_value = batch_mock

    def test_returns_form_info(
        self, client, mock_service, fake_create_response, fake_batch_update_response
    ) -> None:
        """create_form returns a FormInfo instance on success."""
        self._setup_service(mock_service, fake_create_response, fake_batch_update_response)
        info = client.create_form({"title": "Test Form"})
        assert isinstance(info, FormInfo)
        assert info.form_id == "abc123"

    def test_responder_uri_is_set(
        self, client, mock_service, fake_create_response
    ) -> None:
        """responder_uri is populated from the API response."""
        self._setup_service(mock_service, fake_create_response)
        info = client.create_form({"title": "Test Form"})
        assert info.responder_uri == "https://docs.google.com/forms/d/abc123/viewform"

    def test_accepts_form_config_object(
        self, client, mock_service, fake_create_response
    ) -> None:
        """create_form accepts a FormConfig object, not just a dict."""
        from gformlib.utils import parse_form_config

        self._setup_service(mock_service, fake_create_response)
        cfg = parse_form_config({"title": "Test Form"})
        info = client.create_form(cfg)
        assert info.form_id == "abc123"

    def test_batch_update_called_with_questions(
        self, client, mock_service, fake_create_response
    ) -> None:
        """batchUpdate is called when questions are present."""
        self._setup_service(mock_service, fake_create_response)
        client.create_form(
            {
                "title": "Test Form",
                "questions": [{"title": "Q", "type": "short_answer"}],
            }
        )
        mock_service.forms.return_value.batchUpdate.assert_called_once()

    def test_batch_update_not_called_when_empty(
        self, client, mock_service, fake_create_response
    ) -> None:
        """batchUpdate is NOT called when there are no questions or description."""
        self._setup_service(mock_service, fake_create_response)
        client.create_form({"title": "Test Form"})
        mock_service.forms.return_value.batchUpdate.assert_not_called()

    def test_invalid_config_raises(self, client) -> None:
        """An invalid config dict raises InvalidConfigError before any API call."""
        with pytest.raises(InvalidConfigError):
            client.create_form({"description": "No title"})

    def test_api_error_on_create_raises_form_creation_error(
        self, client, mock_service
    ) -> None:
        """An HttpError from forms().create() is wrapped in FormCreationError."""
        mock_service.forms.return_value.create.return_value.execute.side_effect = (
            _make_http_error(500)
        )
        with pytest.raises(FormCreationError):
            client.create_form({"title": "Test Form"})

    def test_api_error_on_batch_update_raises_form_update_error(
        self, client, mock_service, fake_create_response
    ) -> None:
        """An HttpError from batchUpdate is wrapped in FormUpdateError."""
        mock_service.forms.return_value.create.return_value.execute.return_value = (
            fake_create_response
        )
        mock_service.forms.return_value.batchUpdate.return_value.execute.side_effect = (
            _make_http_error(400)
        )
        with pytest.raises(FormUpdateError):
            client.create_form(
                {
                    "title": "Test Form",
                    "questions": [{"title": "Q", "type": "short_answer"}],
                }
            )


# ─────────────────────────────────────────────────────────────────────────────
# get_form
# ─────────────────────────────────────────────────────────────────────────────


class TestGetForm:
    """Tests for :meth:`GoogleFormsClient.get_form`."""

    def test_returns_dict(self, client, mock_service) -> None:
        """get_form returns the raw API response dict."""
        expected = {"formId": "abc123", "info": {"title": "T"}}
        mock_service.forms.return_value.get.return_value.execute.return_value = expected
        result = client.get_form("abc123")
        assert result == expected

    def test_http_error_raises_api_error(self, client, mock_service) -> None:
        """An HttpError from forms().get() is wrapped in APIError."""
        mock_service.forms.return_value.get.return_value.execute.side_effect = (
            _make_http_error(404)
        )
        with pytest.raises(APIError):
            client.get_form("nonexistent")


# ─────────────────────────────────────────────────────────────────────────────
# list_responses
# ─────────────────────────────────────────────────────────────────────────────


class TestListResponses:
    """Tests for :meth:`GoogleFormsClient.list_responses`."""

    def test_returns_all_responses_single_page(self, client, mock_service) -> None:
        """list_responses returns all responses from a single page."""
        mock_service.forms.return_value.responses.return_value.list.return_value.execute.return_value = {
            "responses": [{"responseId": "r1"}, {"responseId": "r2"}]
        }
        results = client.list_responses("abc123")
        assert len(results) == 2

    def test_handles_empty_responses(self, client, mock_service) -> None:
        """list_responses returns an empty list when there are no responses."""
        mock_service.forms.return_value.responses.return_value.list.return_value.execute.return_value = {}
        results = client.list_responses("abc123")
        assert results == []

    def test_pagination(self, client, mock_service) -> None:
        """list_responses follows nextPageToken across multiple pages."""
        page1 = {"responses": [{"responseId": "r1"}], "nextPageToken": "tok1"}
        page2 = {"responses": [{"responseId": "r2"}]}
        mock_service.forms.return_value.responses.return_value.list.return_value.execute.side_effect = [
            page1,
            page2,
        ]
        results = client.list_responses("abc123")
        assert len(results) == 2
        assert mock_service.forms.return_value.responses.return_value.list.call_count == 2

    def test_http_error_raises_api_error(self, client, mock_service) -> None:
        """An HttpError from list() is wrapped in APIError."""
        mock_service.forms.return_value.responses.return_value.list.return_value.execute.side_effect = (
            _make_http_error(403)
        )
        with pytest.raises(APIError):
            client.list_responses("abc123")
