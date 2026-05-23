"""Google Forms API request builder.

This module converts a validated :class:`~gformlib.models.FormConfig` into
the JSON structures expected by the
`Google Forms REST API v1 <https://developers.google.com/forms/api/reference/rest>`_.

The main entry-point is :class:`FormBuilder`.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .models import FormConfig, QuestionConfig, QuestionType


class FormBuilder:
    """Converts a :class:`~gformlib.models.FormConfig` into Google Forms API payloads.

    This class is used internally by :class:`~gformlib.client.GoogleFormsClient`
    but is also exposed publicly so that callers can inspect or further
    customise the generated request bodies before submitting them.

    Example::

        from gformlib.builder import FormBuilder
        from gformlib.models import FormConfig, QuestionConfig, QuestionType

        config = FormConfig(
            title="Demo",
            questions=[
                QuestionConfig(
                    title="Favourite colour?",
                    question_type=QuestionType.SHORT_ANSWER,
                ),
            ],
        )
        builder = FormBuilder(config)
        create_body = builder.build_create_body()
        batch_body  = builder.build_batch_update_body()
    """

    def __init__(self, config: FormConfig) -> None:
        """Initialise the builder with a validated form configuration.

        Args:
            config: A :class:`~gformlib.models.FormConfig` instance.
                Use :func:`~gformlib.utils.parse_form_config` to obtain
                one from a raw dict.
        """
        self._config = config

    # ──────────────────────────────────────────────────────────────────────
    # Public helpers
    # ──────────────────────────────────────────────────────────────────────

    def build_create_body(self) -> Dict[str, Any]:
        """Build the request body for the ``forms().create()`` API call.

        Returns:
            A dict suitable for passing as the ``body`` argument of
            ``service.forms().create(body=...)``.  Contains only the form
            title and document title; questions are added separately via
            :meth:`build_batch_update_body`.

        Example::

            body = builder.build_create_body()
            # {"info": {"title": "Demo", "documentTitle": "Demo"}}
        """
        return {
            "info": {
                "title": self._config.title,
                "documentTitle": self._config.document_title or self._config.title,
            }
        }

    def build_batch_update_body(self) -> Dict[str, Any]:
        """Build the ``batchUpdate`` request body that adds all questions.

        Returns:
            A dict suitable for passing as the ``body`` argument of
            ``service.forms().batchUpdate(formId=..., body=...)``.
            Returns an empty ``{"requests": []}`` dict when the form has
            no questions.

        Example::

            body = builder.build_batch_update_body()
            # {"requests": [{"createItem": {...}}, ...]}
        """
        requests: List[Dict[str, Any]] = []

        # Optionally set the form description via an updateFormInfo request
        if self._config.description:
            requests.append(self._build_update_form_info_request())

        for index, question in enumerate(self._config.questions):
            requests.append(self._build_create_item_request(question, index))

        return {"requests": requests}

    # ──────────────────────────────────────────────────────────────────────
    # Private builders
    # ──────────────────────────────────────────────────────────────────────

    def _build_update_form_info_request(self) -> Dict[str, Any]:
        """Return a ``updateFormInfo`` mutation for the form description.

        Returns:
            A single ``updateFormInfo`` request dict.
        """
        return {
            "updateFormInfo": {
                "info": {"description": self._config.description},
                "updateMask": "description",
            }
        }

    def _build_create_item_request(
        self, question: QuestionConfig, index: int
    ) -> Dict[str, Any]:
        """Return a ``createItem`` request for a single question.

        Args:
            question: The question configuration to convert.
            index: Zero-based insertion index (determines question order).

        Returns:
            A ``createItem`` request dict.
        """
        question_body = self._build_question_body(question)

        item: Dict[str, Any] = {
            "title": question.title,
            "questionItem": {"question": question_body},
        }
        if question.description:
            item["description"] = question.description

        return {
            "createItem": {
                "item": item,
                "location": {"index": index},
            }
        }

    def _build_question_body(self, question: QuestionConfig) -> Dict[str, Any]:
        """Build the ``question`` sub-object inside a ``questionItem``.

        Args:
            question: Source question configuration.

        Returns:
            A ``question`` dict containing ``required`` and the
            type-specific sub-key (e.g. ``textQuestion``,
            ``choiceQuestion``).
        """
        body: Dict[str, Any] = {"required": question.required}

        qtype = question.question_type

        if qtype in (QuestionType.SHORT_ANSWER, QuestionType.PARAGRAPH):
            body["textQuestion"] = {"paragraph": qtype == QuestionType.PARAGRAPH}

        elif qtype in (
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.CHECKBOXES,
            QuestionType.DROPDOWN,
        ):
            body["choiceQuestion"] = self._build_choice_question(question)

        elif qtype == QuestionType.SCALE:
            body["scaleQuestion"] = self._build_scale_question(question)

        elif qtype == QuestionType.DATE:
            body["dateQuestion"] = {
                "includeTime": question.include_time,
                "includeYear": question.include_year,
            }

        elif qtype == QuestionType.TIME:
            body["timeQuestion"] = {"duration": question.is_duration}

        elif qtype == QuestionType.FILE_UPLOAD:
            # FILE_UPLOAD requires the form to be in quiz mode and connected
            # to Drive; we emit the minimal required payload here.
            body["fileUploadQuestion"] = {}

        return body

    @staticmethod
    def _build_choice_question(question: QuestionConfig) -> Dict[str, Any]:
        """Build a ``choiceQuestion`` sub-object.

        Args:
            question: Source question configuration.  ``question.options``
                must be a non-empty list.

        Returns:
            A ``choiceQuestion`` dict.
        """
        type_map = {
            QuestionType.MULTIPLE_CHOICE: "RADIO",
            QuestionType.CHECKBOXES: "CHECKBOX",
            QuestionType.DROPDOWN: "DROP_DOWN",
        }
        return {
            "type": type_map[question.question_type],
            "options": [{"value": opt} for opt in (question.options or [])],
            "shuffle": question.shuffle_options,
        }

    @staticmethod
    def _build_scale_question(question: QuestionConfig) -> Dict[str, Any]:
        """Build a ``scaleQuestion`` sub-object.

        Args:
            question: Source question configuration.

        Returns:
            A ``scaleQuestion`` dict.
        """
        payload: Dict[str, Any] = {
            "low": question.low,
            "high": question.high,
        }
        if question.low_label:
            payload["lowLabel"] = question.low_label
        if question.high_label:
            payload["highLabel"] = question.high_label
        return payload
