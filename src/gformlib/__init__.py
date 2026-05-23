"""gformlib – Google Forms from JSON.

A Python library for creating and managing Google Forms programmatically,
wrapping the official `Google Forms API v1`_.

.. _Google Forms API v1: https://developers.google.com/forms/api/reference/rest

Quickstart::

    from gformlib import GoogleFormsClient

    client = GoogleFormsClient.from_service_account("service_account.json")
    info = client.create_form(
        {
            "title": "My Survey",
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

from .builder import FormBuilder
from .client import DEFAULT_SCOPES, GoogleFormsClient
from .exceptions import (
    APIError,
    AuthenticationError,
    FormCreationError,
    FormUpdateError,
    GFormLibError,
    InvalidConfigError,
)
from .models import FormConfig, FormInfo, QuestionConfig, QuestionType, UpdateFormConfig
from .utils import parse_form_config, parse_question, parse_update_config

__all__ = [
    # Client
    "GoogleFormsClient",
    "DEFAULT_SCOPES",
    # Builder
    "FormBuilder",
    # Models
    "FormConfig",
    "FormInfo",
    "QuestionConfig",
    "QuestionType",
    "UpdateFormConfig",
    # Utils
    "parse_form_config",
    "parse_question",
    "parse_update_config",
    # Exceptions
    "GFormLibError",
    "AuthenticationError",
    "FormCreationError",
    "FormUpdateError",
    "InvalidConfigError",
    "APIError",
]

__version__ = "0.2.0"
__author__ = "Andhitia Rama"
__email__ = "andhitia.r@gmail.com"
