"""Unit tests for :mod:`gformlib.utils`."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from gformlib.exceptions import InvalidConfigError
from gformlib.models import FormConfig, QuestionConfig, QuestionType
from gformlib.utils import parse_form_config, parse_question


class TestParseQuestion:
    """Tests for :func:`parse_question`."""

    def test_minimal_short_answer(self) -> None:
        """Minimal short-answer question parses without error."""
        q = parse_question({"title": "Name?", "type": "short_answer"})
        assert q.title == "Name?"
        assert q.question_type == QuestionType.SHORT_ANSWER
        assert q.required is False

    def test_required_field(self) -> None:
        """'required' key is respected."""
        q = parse_question({"title": "Q", "type": "paragraph", "required": True})
        assert q.required is True

    def test_multiple_choice_with_options(self) -> None:
        """Multiple-choice question with options parses correctly."""
        q = parse_question(
            {
                "title": "Colour",
                "type": "multiple_choice",
                "options": ["Red", "Blue"],
            }
        )
        assert q.question_type == QuestionType.MULTIPLE_CHOICE
        assert q.options == ["Red", "Blue"]

    def test_checkboxes_with_options(self) -> None:
        """Checkboxes question with options parses correctly."""
        q = parse_question(
            {"title": "Toppings", "type": "checkboxes", "options": ["A", "B"]}
        )
        assert q.question_type == QuestionType.CHECKBOXES

    def test_dropdown_with_options(self) -> None:
        """Dropdown question with options parses correctly."""
        q = parse_question(
            {"title": "Size", "type": "dropdown", "options": ["S", "M", "L"]}
        )
        assert q.question_type == QuestionType.DROPDOWN

    def test_scale_defaults(self) -> None:
        """Scale question uses default low=1 / high=5 when not supplied."""
        q = parse_question({"title": "Rate", "type": "scale"})
        assert q.low == 1
        assert q.high == 5

    def test_scale_custom_range(self) -> None:
        """Scale question accepts custom low/high values."""
        q = parse_question({"title": "Rate", "type": "scale", "low": 0, "high": 10})
        assert q.low == 0
        assert q.high == 10

    def test_scale_with_labels(self) -> None:
        """Scale labels are stored on the QuestionConfig."""
        q = parse_question(
            {
                "title": "Rate",
                "type": "scale",
                "low": 1,
                "high": 5,
                "low_label": "Poor",
                "high_label": "Excellent",
            }
        )
        assert q.low_label == "Poor"
        assert q.high_label == "Excellent"

    def test_date_question(self) -> None:
        """Date question parses include_time and include_year flags."""
        q = parse_question(
            {"title": "DOB", "type": "date", "include_time": True, "include_year": False}
        )
        assert q.question_type == QuestionType.DATE
        assert q.include_time is True
        assert q.include_year is False

    def test_time_question(self) -> None:
        """Time question parses is_duration flag."""
        q = parse_question({"title": "Duration", "type": "time", "is_duration": True})
        assert q.question_type == QuestionType.TIME
        assert q.is_duration is True

    def test_file_upload_question(self) -> None:
        """File upload question parses without error."""
        q = parse_question({"title": "Upload", "type": "file_upload"})
        assert q.question_type == QuestionType.FILE_UPLOAD

    # ── Error cases ──────────────────────────────────────────────────────────

    def test_missing_title_raises(self) -> None:
        """Missing 'title' raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="title"):
            parse_question({"type": "short_answer"})

    def test_missing_type_raises(self) -> None:
        """Missing 'type' raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="type"):
            parse_question({"title": "Q"})

    def test_unknown_type_raises(self) -> None:
        """An unknown question type raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="unknown question type"):
            parse_question({"title": "Q", "type": "magic_wand"})

    def test_choice_missing_options_raises(self) -> None:
        """Choice question without options raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="options"):
            parse_question({"title": "Q", "type": "multiple_choice"})

    def test_choice_empty_options_raises(self) -> None:
        """Choice question with empty options list raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="options"):
            parse_question({"title": "Q", "type": "multiple_choice", "options": []})

    def test_scale_low_gte_high_raises(self) -> None:
        """Scale question where low >= high raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="low"):
            parse_question({"title": "Q", "type": "scale", "low": 5, "high": 5})

    def test_scale_non_int_low_raises(self) -> None:
        """Scale question where low is not int raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError):
            parse_question({"title": "Q", "type": "scale", "low": "bad", "high": 5})

    def test_error_contains_field(self) -> None:
        """InvalidConfigError.field is set to the failing key path."""
        with pytest.raises(InvalidConfigError) as exc_info:
            parse_question({"type": "short_answer"}, index=2)
        assert exc_info.value.field == "questions[2].title"


class TestParseFormConfig:
    """Tests for :func:`parse_form_config`."""

    def test_minimal_form(self) -> None:
        """Minimal form with just a title parses successfully."""
        cfg = parse_form_config({"title": "My Form"})
        assert isinstance(cfg, FormConfig)
        assert cfg.title == "My Form"
        assert cfg.questions == []

    def test_document_title_defaults_to_title(self) -> None:
        """document_title defaults to title when not provided."""
        cfg = parse_form_config({"title": "Survey"})
        assert cfg.document_title == "Survey"

    def test_explicit_document_title(self) -> None:
        """Explicit document_title is respected."""
        cfg = parse_form_config({"title": "Survey", "document_title": "Doc Title"})
        assert cfg.document_title == "Doc Title"

    def test_description_is_stored(self) -> None:
        """Description is preserved."""
        cfg = parse_form_config({"title": "T", "description": "Hello"})
        assert cfg.description == "Hello"

    def test_questions_are_parsed(self) -> None:
        """Questions list is parsed into QuestionConfig objects."""
        cfg = parse_form_config(
            {
                "title": "T",
                "questions": [
                    {"title": "Q1", "type": "short_answer"},
                    {"title": "Q2", "type": "paragraph"},
                ],
            }
        )
        assert len(cfg.questions) == 2
        assert isinstance(cfg.questions[0], QuestionConfig)

    def test_title_is_stripped(self) -> None:
        """Leading/trailing whitespace in title is stripped."""
        cfg = parse_form_config({"title": "  Padded  "})
        assert cfg.title == "Padded"

    # ── Error cases ──────────────────────────────────────────────────────────

    def test_non_dict_raises_type_error(self) -> None:
        """Passing a non-dict raises TypeError."""
        with pytest.raises(TypeError, match="dict"):
            parse_form_config("not a dict")  # type: ignore[arg-type]

    def test_missing_title_raises(self) -> None:
        """Missing title key raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="title"):
            parse_form_config({"description": "No title here"})

    def test_empty_title_raises(self) -> None:
        """Blank title raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="title"):
            parse_form_config({"title": "   "})

    def test_non_list_questions_raises(self) -> None:
        """Non-list 'questions' raises InvalidConfigError."""
        with pytest.raises(InvalidConfigError, match="questions"):
            parse_form_config({"title": "T", "questions": "not a list"})

    def test_invalid_question_propagates(self) -> None:
        """An invalid question in the list propagates its error."""
        with pytest.raises(InvalidConfigError):
            parse_form_config(
                {"title": "T", "questions": [{"type": "short_answer"}]}
            )
