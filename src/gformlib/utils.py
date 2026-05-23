"""Validation utilities for gformlib.

This module provides helpers that validate user-supplied configuration
dictionaries and convert them into typed :mod:`gformlib.models` objects
*before* any API call is made.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .exceptions import InvalidConfigError
from .models import FormConfig, QuestionConfig, QuestionType, UpdateFormConfig

#: Question types that require an ``options`` list.
_CHOICE_TYPES: frozenset[QuestionType] = frozenset(
    {
        QuestionType.MULTIPLE_CHOICE,
        QuestionType.CHECKBOXES,
        QuestionType.DROPDOWN,
    }
)

#: Mapping from the user-facing string to the :class:`~gformlib.models.QuestionType` member.
_TYPE_ALIASES: Dict[str, QuestionType] = {member.value: member for member in QuestionType}


def parse_question(data: Dict[str, Any], index: int = 0) -> QuestionConfig:
    """Parse and validate a single question configuration dict.

    Args:
        data: Raw question configuration dict supplied by the caller.
            Must contain at least ``"title"`` and ``"type"`` keys.
        index: Zero-based position of the question in the form (used in
            error messages).

    Returns:
        A validated :class:`~gformlib.models.QuestionConfig` instance.

    Raises:
        InvalidConfigError: If a required key is missing, the type is
            unknown, or type-specific constraints are violated.

    Example::

        from gformlib.utils import parse_question

        q = parse_question(
            {"title": "Pick one", "type": "multiple_choice", "options": ["A", "B"]},
            index=0,
        )
    """
    prefix = f"questions[{index}]"

    if "title" not in data:
        raise InvalidConfigError(
            f"{prefix}: missing required key 'title'.",
            field=f"{prefix}.title",
        )

    raw_type = data.get("type")
    if raw_type is None:
        raise InvalidConfigError(
            f"{prefix}: missing required key 'type'.",
            field=f"{prefix}.type",
        )

    question_type = _TYPE_ALIASES.get(str(raw_type).lower())
    if question_type is None:
        valid = ", ".join(sorted(_TYPE_ALIASES.keys()))
        raise InvalidConfigError(
            f"{prefix}: unknown question type '{raw_type}'. Valid types: {valid}.",
            field=f"{prefix}.type",
        )

    # Validate choice-type questions
    if question_type in _CHOICE_TYPES:
        options = data.get("options")
        if not options or not isinstance(options, list):
            raise InvalidConfigError(
                f"{prefix}: question type '{raw_type}' requires a non-empty 'options' list.",
                field=f"{prefix}.options",
            )
        if len(options) < 1:
            raise InvalidConfigError(
                f"{prefix}: 'options' must contain at least one item.",
                field=f"{prefix}.options",
            )

    # Validate scale questions
    if question_type == QuestionType.SCALE:
        low = data.get("low", 1)
        high = data.get("high", 5)
        if not isinstance(low, int) or not isinstance(high, int):
            raise InvalidConfigError(
                f"{prefix}: 'low' and 'high' must be integers for scale questions.",
                field=f"{prefix}.low",
            )
        if low >= high:
            raise InvalidConfigError(
                f"{prefix}: 'low' ({low}) must be less than 'high' ({high}).",
                field=f"{prefix}.low",
            )

    return QuestionConfig(
        title=str(data["title"]),
        question_type=question_type,
        required=bool(data.get("required", False)),
        description=data.get("description"),
        options=list(data["options"]) if data.get("options") else None,
        shuffle_options=bool(data.get("shuffle_options", False)),
        low=int(data.get("low", 1)),
        high=int(data.get("high", 5)),
        low_label=data.get("low_label"),
        high_label=data.get("high_label"),
        include_time=bool(data.get("include_time", False)),
        include_year=bool(data.get("include_year", True)),
        is_duration=bool(data.get("is_duration", False)),
    )


def parse_form_config(data: Dict[str, Any]) -> FormConfig:
    """Parse and validate a complete form configuration dict.

    Args:
        data: Raw form configuration dict.  Must contain at least a
            ``"title"`` key.  The optional ``"questions"`` key should be
            a list of question dicts (see :func:`parse_question`).

    Returns:
        A validated :class:`~gformlib.models.FormConfig` instance.

    Raises:
        InvalidConfigError: If the configuration is structurally invalid.
        TypeError: If *data* is not a dict.

    Example::

        from gformlib.utils import parse_form_config

        cfg = parse_form_config(
            {
                "title": "My Survey",
                "questions": [
                    {"title": "Name?", "type": "short_answer"},
                ],
            }
        )
    """
    if not isinstance(data, dict):
        raise TypeError(f"Form configuration must be a dict, got {type(data).__name__}.")

    if "title" not in data or not str(data["title"]).strip():
        raise InvalidConfigError(
            "Form configuration must have a non-empty 'title'.",
            field="title",
        )

    raw_questions: List[Dict[str, Any]] = data.get("questions") or []
    if not isinstance(raw_questions, list):
        raise InvalidConfigError(
            "'questions' must be a list.",
            field="questions",
        )

    questions = [parse_question(q, i) for i, q in enumerate(raw_questions)]

    return FormConfig(
        title=str(data["title"]).strip(),
        document_title=data.get("document_title") or str(data["title"]).strip(),
        description=data.get("description"),
        questions=questions,
    )


def parse_update_config(data: Dict[str, Any]) -> UpdateFormConfig:
    """Parse and validate a form update configuration dict.

    All keys are optional.  At least one of ``title``, ``description``, or
    ``add_questions`` should normally be present, though an empty update is
    accepted (it simply returns the current form state unchanged).

    Args:
        data: Raw update configuration dict.  Recognised keys:

            * ``"title"`` *(str)* – new form title.
            * ``"description"`` *(str)* – new form description.
            * ``"add_questions"`` *(list)* – question dicts to append
              (same format as in :func:`parse_form_config`).

    Returns:
        A validated :class:`~gformlib.models.UpdateFormConfig` instance.

    Raises:
        InvalidConfigError: If ``add_questions`` is present but not a list,
            or if any individual question dict is invalid.
        TypeError: If *data* is not a dict.

    Example::

        from gformlib.utils import parse_update_config

        cfg = parse_update_config(
            {
                "title": "Revised Survey",
                "add_questions": [
                    {"title": "Comments", "type": "paragraph"},
                ],
            }
        )
    """
    if not isinstance(data, dict):
        raise TypeError(f"Update configuration must be a dict, got {type(data).__name__}.")

    raw_questions: List[Dict[str, Any]] = data.get("add_questions") or []
    if not isinstance(raw_questions, list):
        raise InvalidConfigError(
            "'add_questions' must be a list.",
            field="add_questions",
        )

    questions = [parse_question(q, i) for i, q in enumerate(raw_questions)]

    return UpdateFormConfig(
        title=str(data["title"]).strip() if data.get("title") else None,
        description=data.get("description"),
        add_questions=questions,
    )
