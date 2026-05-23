"""Data models used throughout gformlib.

This module provides:

* :class:`QuestionType` – enumeration of supported question types.
* :class:`QuestionConfig` – configuration for a single question.
* :class:`FormConfig` – configuration for an entire form.
* :class:`FormInfo` – metadata returned after a form is created.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class QuestionType(str, Enum):
    """Supported question types for Google Forms.

    Each member corresponds to a question variant in the
    `Google Forms API <https://developers.google.com/forms/api/reference/rest>`_.

    Example::

        from gformlib.models import QuestionType
        qt = QuestionType.MULTIPLE_CHOICE
    """

    SHORT_ANSWER = "short_answer"
    """Single-line free-text input (``TextQuestion`` with ``paragraph=False``)."""

    PARAGRAPH = "paragraph"
    """Multi-line free-text input (``TextQuestion`` with ``paragraph=True``)."""

    MULTIPLE_CHOICE = "multiple_choice"
    """Radio-button selection – respondent picks exactly one option."""

    CHECKBOXES = "checkboxes"
    """Checkbox selection – respondent may pick multiple options."""

    DROPDOWN = "dropdown"
    """Dropdown menu – respondent picks exactly one option."""

    SCALE = "scale"
    """Linear scale – respondent picks a number between ``low`` and ``high``."""

    DATE = "date"
    """Date picker, optionally including time and/or year."""

    TIME = "time"
    """Time-of-day picker or duration input."""

    FILE_UPLOAD = "file_upload"
    """File upload widget (requires Google Drive integration)."""


@dataclass
class QuestionConfig:
    """Configuration for a single Google Form question.

    Example::

        from gformlib.models import QuestionConfig, QuestionType

        q = QuestionConfig(
            title="Rate our service",
            question_type=QuestionType.SCALE,
            required=True,
            low=1,
            high=10,
            low_label="Poor",
            high_label="Excellent",
        )
    """

    title: str
    """The question text displayed to respondents."""

    question_type: QuestionType
    """The type of question."""

    required: bool = False
    """Whether a response is required."""

    description: Optional[str] = None
    """Optional help text shown below the question."""

    # ── Choice questions ────────────────────────────────────────────────────
    options: Optional[List[str]] = None
    """Answer options (required for choice-type questions)."""

    shuffle_options: bool = False
    """Randomise the order of answer options."""

    # ── Scale questions ─────────────────────────────────────────────────────
    low: int = 1
    """Minimum value for scale questions."""

    high: int = 5
    """Maximum value for scale questions."""

    low_label: Optional[str] = None
    """Descriptive label for the low end of the scale."""

    high_label: Optional[str] = None
    """Descriptive label for the high end of the scale."""

    # ── Date questions ──────────────────────────────────────────────────────
    include_time: bool = False
    """Include time picker in date questions."""

    include_year: bool = True
    """Include year in date questions."""

    # ── Time questions ──────────────────────────────────────────────────────
    is_duration: bool = False
    """Treat time question as duration instead of time-of-day."""


@dataclass
class FormConfig:
    """Configuration for a complete Google Form.

    Example::

        from gformlib.models import FormConfig, QuestionConfig, QuestionType

        config = FormConfig(
            title="Customer Survey",
            description="Help us improve our service.",
            questions=[
                QuestionConfig(
                    title="Your name",
                    question_type=QuestionType.SHORT_ANSWER,
                    required=True,
                ),
            ],
        )
    """

    title: str
    """The displayed title of the form."""

    questions: List[QuestionConfig] = field(default_factory=list)
    """Ordered list of questions."""

    document_title: Optional[str] = None
    """Google Docs document title (defaults to ``title``)."""

    description: Optional[str] = None
    """Optional introductory description for the form."""


@dataclass
class UpdateFormConfig:
    """Configuration for updating an existing Google Form.

    All fields are optional.  Only the fields that are set will be changed
    in the live form; fields left as ``None`` are left untouched.

    Example::

        from gformlib.models import UpdateFormConfig, QuestionConfig, QuestionType

        update = UpdateFormConfig(
            title="Revised Survey",
            description="Updated description.",
            add_questions=[
                QuestionConfig(
                    title="New question",
                    question_type=QuestionType.SHORT_ANSWER,
                    required=True,
                ),
            ],
        )
    """

    title: Optional[str] = None
    """New title for the form.  ``None`` leaves the title unchanged."""

    description: Optional[str] = None
    """New description for the form.  ``None`` leaves it unchanged."""

    add_questions: List[QuestionConfig] = field(default_factory=list)
    """Questions to append after the existing items in the form."""


@dataclass
class FormInfo:
    """Metadata about a Google Form that has been created via the API.

    Instances of this class are returned by
    :meth:`~gformlib.client.GoogleFormsClient.create_form`.

    Example::

        info = client.create_form(config)
        print(info.responder_uri)  # share this link
    """

    form_id: str
    """Unique identifier of the form."""

    title: str
    """Displayed title of the form."""

    document_title: str
    """Title of the backing Google Docs document."""

    responder_uri: str
    """URL that respondents use to fill in the form."""

    linked_sheet_id: Optional[str] = None
    """ID of the linked Google Sheet (if response collection is enabled)."""

    revision_id: Optional[str] = None
    """Revision ID returned by the API."""

    raw: Optional[Dict[str, Any]] = field(default=None, repr=False)
    """Raw API response dict."""
