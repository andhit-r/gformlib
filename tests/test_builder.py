"""Unit tests for :mod:`gformlib.builder`."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from gformlib.builder import FormBuilder
from gformlib.models import FormConfig, QuestionConfig, QuestionType


def _make_builder(title: str = "T", questions=None, description=None) -> FormBuilder:
    config = FormConfig(
        title=title,
        document_title=title,
        description=description,
        questions=questions or [],
    )
    return FormBuilder(config)


class TestBuildCreateBody:
    """Tests for :meth:`FormBuilder.build_create_body`."""

    def test_returns_info_with_title(self) -> None:
        """create body contains info.title."""
        body = _make_builder("My Form").build_create_body()
        assert body["info"]["title"] == "My Form"

    def test_returns_info_with_document_title(self) -> None:
        """create body contains info.documentTitle."""
        body = _make_builder("My Form").build_create_body()
        assert body["info"]["documentTitle"] == "My Form"

    def test_document_title_can_differ(self) -> None:
        """documentTitle uses the config's document_title value."""
        config = FormConfig(title="Form", document_title="Doc Title")
        body = FormBuilder(config).build_create_body()
        assert body["info"]["documentTitle"] == "Doc Title"


class TestBuildBatchUpdateBody:
    """Tests for :meth:`FormBuilder.build_batch_update_body`."""

    def test_empty_form_returns_empty_requests(self) -> None:
        """Form with no questions and no description returns empty requests."""
        body = _make_builder().build_batch_update_body()
        assert body == {"requests": []}

    def test_description_adds_update_form_info_request(self) -> None:
        """A description adds an updateFormInfo request at the start."""
        body = _make_builder(description="Hello").build_batch_update_body()
        assert body["requests"][0].get("updateFormInfo") is not None
        assert body["requests"][0]["updateFormInfo"]["info"]["description"] == "Hello"

    def test_question_count_matches(self) -> None:
        """One createItem request is generated per question."""
        questions = [
            QuestionConfig(title="Q1", question_type=QuestionType.SHORT_ANSWER),
            QuestionConfig(title="Q2", question_type=QuestionType.PARAGRAPH),
        ]
        body = _make_builder(questions=questions).build_batch_update_body()
        create_items = [r for r in body["requests"] if "createItem" in r]
        assert len(create_items) == 2

    def test_question_index_is_set(self) -> None:
        """Each createItem request has the correct location.index."""
        questions = [
            QuestionConfig(title=f"Q{i}", question_type=QuestionType.SHORT_ANSWER)
            for i in range(3)
        ]
        body = _make_builder(questions=questions).build_batch_update_body()
        create_items = [r["createItem"] for r in body["requests"] if "createItem" in r]
        for i, item in enumerate(create_items):
            assert item["location"]["index"] == i

    def test_question_title_is_set(self) -> None:
        """The title field on each createItem matches the QuestionConfig."""
        questions = [QuestionConfig(title="My Q", question_type=QuestionType.DATE)]
        body = _make_builder(questions=questions).build_batch_update_body()
        create_item = body["requests"][0]["createItem"]
        assert create_item["item"]["title"] == "My Q"

    def test_question_description_included_when_set(self) -> None:
        """A question with a description includes it in the item."""
        questions = [
            QuestionConfig(
                title="Q",
                question_type=QuestionType.SHORT_ANSWER,
                description="Some help",
            )
        ]
        body = _make_builder(questions=questions).build_batch_update_body()
        item = body["requests"][0]["createItem"]["item"]
        assert item.get("description") == "Some help"

    def test_question_description_omitted_when_none(self) -> None:
        """A question without a description omits the description key."""
        questions = [QuestionConfig(title="Q", question_type=QuestionType.SHORT_ANSWER)]
        body = _make_builder(questions=questions).build_batch_update_body()
        item = body["requests"][0]["createItem"]["item"]
        assert "description" not in item


class TestBuildQuestionBodies:
    """Tests for type-specific question sub-objects."""

    def _question_body(self, question: QuestionConfig) -> Dict[str, Any]:
        builder = FormBuilder(FormConfig(title="T", questions=[question]))
        batch = builder.build_batch_update_body()
        return batch["requests"][0]["createItem"]["item"]["questionItem"]["question"]

    def test_short_answer(self) -> None:
        """SHORT_ANSWER maps to textQuestion with paragraph=False."""
        body = self._question_body(
            QuestionConfig(title="Q", question_type=QuestionType.SHORT_ANSWER)
        )
        assert body["textQuestion"] == {"paragraph": False}

    def test_paragraph(self) -> None:
        """PARAGRAPH maps to textQuestion with paragraph=True."""
        body = self._question_body(
            QuestionConfig(title="Q", question_type=QuestionType.PARAGRAPH)
        )
        assert body["textQuestion"] == {"paragraph": True}

    def test_multiple_choice(self) -> None:
        """MULTIPLE_CHOICE maps to choiceQuestion with type=RADIO."""
        body = self._question_body(
            QuestionConfig(
                title="Q",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["A", "B"],
            )
        )
        assert body["choiceQuestion"]["type"] == "RADIO"
        assert body["choiceQuestion"]["options"] == [{"value": "A"}, {"value": "B"}]

    def test_checkboxes(self) -> None:
        """CHECKBOXES maps to choiceQuestion with type=CHECKBOX."""
        body = self._question_body(
            QuestionConfig(
                title="Q",
                question_type=QuestionType.CHECKBOXES,
                options=["X"],
            )
        )
        assert body["choiceQuestion"]["type"] == "CHECKBOX"

    def test_dropdown(self) -> None:
        """DROPDOWN maps to choiceQuestion with type=DROP_DOWN."""
        body = self._question_body(
            QuestionConfig(
                title="Q",
                question_type=QuestionType.DROPDOWN,
                options=["S", "M"],
            )
        )
        assert body["choiceQuestion"]["type"] == "DROP_DOWN"

    def test_shuffle_options(self) -> None:
        """shuffle_options is forwarded to choiceQuestion.shuffle."""
        body = self._question_body(
            QuestionConfig(
                title="Q",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["A"],
                shuffle_options=True,
            )
        )
        assert body["choiceQuestion"]["shuffle"] is True

    def test_scale_defaults(self) -> None:
        """SCALE uses default low/high values."""
        body = self._question_body(
            QuestionConfig(title="Q", question_type=QuestionType.SCALE)
        )
        assert body["scaleQuestion"]["low"] == 1
        assert body["scaleQuestion"]["high"] == 5

    def test_scale_with_labels(self) -> None:
        """SCALE forwards lowLabel and highLabel when set."""
        body = self._question_body(
            QuestionConfig(
                title="Q",
                question_type=QuestionType.SCALE,
                low_label="Bad",
                high_label="Good",
            )
        )
        assert body["scaleQuestion"]["lowLabel"] == "Bad"
        assert body["scaleQuestion"]["highLabel"] == "Good"

    def test_scale_without_labels(self) -> None:
        """SCALE omits lowLabel/highLabel when not set."""
        body = self._question_body(
            QuestionConfig(title="Q", question_type=QuestionType.SCALE)
        )
        assert "lowLabel" not in body["scaleQuestion"]
        assert "highLabel" not in body["scaleQuestion"]

    def test_date_default_flags(self) -> None:
        """DATE defaults to includeTime=False, includeYear=True."""
        body = self._question_body(
            QuestionConfig(title="Q", question_type=QuestionType.DATE)
        )
        assert body["dateQuestion"]["includeTime"] is False
        assert body["dateQuestion"]["includeYear"] is True

    def test_date_with_time(self) -> None:
        """DATE respects include_time=True."""
        body = self._question_body(
            QuestionConfig(
                title="Q", question_type=QuestionType.DATE, include_time=True
            )
        )
        assert body["dateQuestion"]["includeTime"] is True

    def test_time_default(self) -> None:
        """TIME defaults to duration=False."""
        body = self._question_body(
            QuestionConfig(title="Q", question_type=QuestionType.TIME)
        )
        assert body["timeQuestion"]["duration"] is False

    def test_time_duration(self) -> None:
        """TIME respects is_duration=True."""
        body = self._question_body(
            QuestionConfig(
                title="Q", question_type=QuestionType.TIME, is_duration=True
            )
        )
        assert body["timeQuestion"]["duration"] is True

    def test_file_upload(self) -> None:
        """FILE_UPLOAD produces a fileUploadQuestion sub-key."""
        body = self._question_body(
            QuestionConfig(title="Q", question_type=QuestionType.FILE_UPLOAD)
        )
        assert "fileUploadQuestion" in body

    def test_required_flag_forwarded(self) -> None:
        """required=True is forwarded to the question body."""
        body = self._question_body(
            QuestionConfig(
                title="Q",
                question_type=QuestionType.SHORT_ANSWER,
                required=True,
            )
        )
        assert body["required"] is True
