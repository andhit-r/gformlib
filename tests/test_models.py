"""Unit tests for :mod:`gformlib.models`."""

from __future__ import annotations

import pytest

from gformlib.models import FormConfig, FormInfo, QuestionConfig, QuestionType


class TestQuestionType:
    """Tests for the :class:`QuestionType` enum."""

    def test_all_values_are_strings(self) -> None:
        """Every QuestionType value should be a lowercase string."""
        for member in QuestionType:
            assert isinstance(member.value, str)
            assert member.value == member.value.lower()

    def test_str_comparison(self) -> None:
        """QuestionType inherits from str, so direct string comparison works."""
        assert QuestionType.SHORT_ANSWER == "short_answer"
        assert QuestionType.SCALE == "scale"

    def test_membership(self) -> None:
        """All expected types exist in the enum."""
        expected = {
            "short_answer",
            "paragraph",
            "multiple_choice",
            "checkboxes",
            "dropdown",
            "scale",
            "date",
            "time",
            "file_upload",
        }
        actual = {m.value for m in QuestionType}
        assert expected == actual


class TestQuestionConfig:
    """Tests for the :class:`QuestionConfig` dataclass."""

    def test_defaults(self) -> None:
        """Non-supplied fields should have sensible defaults."""
        q = QuestionConfig(title="Q", question_type=QuestionType.SHORT_ANSWER)
        assert q.required is False
        assert q.description is None
        assert q.options is None
        assert q.shuffle_options is False
        assert q.low == 1
        assert q.high == 5
        assert q.low_label is None
        assert q.high_label is None
        assert q.include_time is False
        assert q.include_year is True
        assert q.is_duration is False

    def test_custom_values(self) -> None:
        """Explicitly supplied values should be stored correctly."""
        q = QuestionConfig(
            title="Rate us",
            question_type=QuestionType.SCALE,
            required=True,
            low=0,
            high=10,
            low_label="Terrible",
            high_label="Amazing",
        )
        assert q.required is True
        assert q.low == 0
        assert q.high == 10
        assert q.low_label == "Terrible"
        assert q.high_label == "Amazing"


class TestFormConfig:
    """Tests for the :class:`FormConfig` dataclass."""

    def test_defaults(self) -> None:
        """FormConfig should have empty questions list by default."""
        config = FormConfig(title="My Form")
        assert config.questions == []
        assert config.description is None
        assert config.document_title is None

    def test_questions_are_stored(self) -> None:
        """Questions passed to the constructor are stored in order."""
        q1 = QuestionConfig(title="Q1", question_type=QuestionType.SHORT_ANSWER)
        q2 = QuestionConfig(title="Q2", question_type=QuestionType.PARAGRAPH)
        config = FormConfig(title="Form", questions=[q1, q2])
        assert len(config.questions) == 2
        assert config.questions[0].title == "Q1"

    def test_questions_default_is_not_shared(self) -> None:
        """Default mutable question list must not be shared between instances."""
        a = FormConfig(title="A")
        b = FormConfig(title="B")
        a.questions.append(QuestionConfig(title="Q", question_type=QuestionType.DATE))
        assert len(b.questions) == 0


class TestFormInfo:
    """Tests for the :class:`FormInfo` dataclass."""

    def test_basic_construction(self) -> None:
        """FormInfo stores all required fields."""
        info = FormInfo(
            form_id="id1",
            title="My Form",
            document_title="My Form Doc",
            responder_uri="https://forms.gle/abc",
        )
        assert info.form_id == "id1"
        assert info.responder_uri == "https://forms.gle/abc"
        assert info.linked_sheet_id is None
        assert info.raw is None

    def test_raw_not_in_repr(self) -> None:
        """The raw field should be excluded from the repr output."""
        info = FormInfo(
            form_id="id1",
            title="T",
            document_title="T",
            responder_uri="https://x",
            raw={"formId": "id1"},
        )
        assert "raw" not in repr(info)
