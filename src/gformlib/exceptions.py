"""Custom exceptions for gformlib.

This module defines the exception hierarchy used throughout the library.
All library-specific exceptions inherit from :class:`GFormLibError`.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class GFormLibError(Exception):
    """Base exception class for all gformlib errors.

    All library-specific exceptions are subclasses of this class, allowing
    callers to catch any gformlib error with a single ``except`` clause::

        try:
            client.create_form(config)
        except GFormLibError as exc:
            print(f"gformlib error: {exc}")
    """


class AuthenticationError(GFormLibError):
    """Raised when authentication with Google APIs fails.

    This may occur when credentials are missing, expired, or lack the
    required OAuth scopes (``forms.body``, ``drive.file``, etc.).

    Example::

        try:
            client = GoogleFormsClient.from_service_account("creds.json")
        except AuthenticationError as exc:
            print(f"Auth failed: {exc}")
    """


class FormCreationError(GFormLibError):
    """Raised when initial form creation via the API fails.

    Wraps errors returned by the ``forms().create()`` call.

    Attributes:
        config: The form configuration dict that triggered the error.
    """

    def __init__(self, message: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialise the exception.

        Args:
            message: Human-readable description of the error.
            config: The raw form configuration dict that caused the error.
        """
        super().__init__(message)
        self.config = config or {}


class FormUpdateError(GFormLibError):
    """Raised when a ``batchUpdate`` call to add questions fails.

    Attributes:
        form_id: The form that was being updated when the error occurred.
    """

    def __init__(self, message: str, form_id: Optional[str] = None) -> None:
        """Initialise the exception.

        Args:
            message: Human-readable description of the error.
            form_id: The ID of the form that was being updated.
        """
        super().__init__(message)
        self.form_id = form_id


class InvalidConfigError(GFormLibError):
    """Raised when the supplied form or question configuration is invalid.

    This is a client-side validation error raised *before* any API call is
    made.

    Attributes:
        field: The configuration field that failed validation (if known).
    """

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        """Initialise the exception.

        Args:
            message: Human-readable description of what is invalid.
            field: Optional dotted field path that failed validation,
                e.g. ``"questions[0].options"``.
        """
        super().__init__(message)
        self.field = field


class APIError(GFormLibError):
    """Raised when the Google Forms API returns an unexpected HTTP error.

    Attributes:
        status_code: HTTP status code returned by the API.
        details: Parsed JSON error body from the API response.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialise the exception.

        Args:
            message: Human-readable description of the API error.
            status_code: HTTP status code (e.g. 403, 500).
            details: Raw error details dict from the API response body.
        """
        super().__init__(message)
        self.status_code = status_code
        self.details: Dict[str, Any] = details or {}
