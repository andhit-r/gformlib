"""Shared pytest fixtures and helpers for the gformlib test suite."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from gformlib.models import FormConfig

# ─────────────────────────────────────────────────────────────────────────────
# Config fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def minimal_form_config_dict() -> Dict[str, Any]:
    """Minimal valid form configuration dict (title only, no questions)."""
    return {"title": "Test Form"}


@pytest.fixture()
def full_form_config_dict() -> Dict[str, Any]:
    """Form configuration dict covering all supported question types."""
    return {
        "title": "Full Survey",
        "document_title": "Full Survey Doc",
        "description": "A comprehensive test form.",
        "questions": [
            {"title": "Your name", "type": "short_answer", "required": True},
            {"title": "Tell us more", "type": "paragraph"},
            {
                "title": "Favourite colour",
                "type": "multiple_choice",
                "options": ["Red", "Green", "Blue"],
                "shuffle_options": True,
            },
            {
                "title": "Toppings",
                "type": "checkboxes",
                "options": ["Cheese", "Mushroom"],
            },
            {
                "title": "Size",
                "type": "dropdown",
                "options": ["Small", "Medium", "Large"],
            },
            {
                "title": "Rating",
                "type": "scale",
                "low": 1,
                "high": 10,
                "low_label": "Poor",
                "high_label": "Excellent",
            },
            {"title": "Birthday", "type": "date", "include_time": False},
            {"title": "Start time", "type": "time"},
        ],
    }


@pytest.fixture()
def minimal_form_config(minimal_form_config_dict: Dict[str, Any]) -> FormConfig:
    """Minimal :class:`~gformlib.models.FormConfig`."""
    from gformlib.utils import parse_form_config

    return parse_form_config(minimal_form_config_dict)


@pytest.fixture()
def full_form_config(full_form_config_dict: Dict[str, Any]) -> FormConfig:
    """Full :class:`~gformlib.models.FormConfig`."""
    from gformlib.utils import parse_form_config

    return parse_form_config(full_form_config_dict)


# ─────────────────────────────────────────────────────────────────────────────
# API response fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def fake_create_response() -> Dict[str, Any]:
    """Simulated ``forms().create()`` API response."""
    return {
        "formId": "abc123",
        "info": {
            "title": "Test Form",
            "documentTitle": "Test Form",
        },
        "responderUri": "https://docs.google.com/forms/d/abc123/viewform",
        "revisionId": "rev1",
    }


@pytest.fixture()
def fake_batch_update_response() -> Dict[str, Any]:
    """Simulated ``forms().batchUpdate()`` API response."""
    return {"form": {"formId": "abc123"}, "replies": []}


# ─────────────────────────────────────────────────────────────────────────────
# Mocked Google client fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_service() -> MagicMock:
    """Return a MagicMock that mimics the Google API service object."""
    return MagicMock()


@pytest.fixture()
def mock_credentials() -> MagicMock:
    """Return a MagicMock that mimics google.oauth2 credentials."""
    creds = MagicMock()
    creds.valid = True
    return creds


@pytest.fixture()
def client(mock_credentials: MagicMock, mock_service: MagicMock) -> Any:
    """Return a :class:`~gformlib.client.GoogleFormsClient` with a mocked service."""
    with patch("gformlib.client.build", return_value=mock_service):
        from gformlib.client import GoogleFormsClient

        return GoogleFormsClient(credentials=mock_credentials)
