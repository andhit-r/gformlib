"""Unit tests for :mod:`gformlib.exceptions`."""

from __future__ import annotations

import pytest

from gformlib.exceptions import (
    APIError,
    AuthenticationError,
    FormCreationError,
    FormUpdateError,
    GFormLibError,
    InvalidConfigError,
)


class TestExceptionHierarchy:
    """All custom exceptions should inherit from GFormLibError."""

    @pytest.mark.parametrize(
        "exc_class",
        [
            AuthenticationError,
            FormCreationError,
            FormUpdateError,
            InvalidConfigError,
            APIError,
        ],
    )
    def test_is_subclass_of_gformliberror(self, exc_class) -> None:
        assert issubclass(exc_class, GFormLibError)

    def test_can_catch_all_with_base(self) -> None:
        """Any derived exception can be caught as GFormLibError."""
        with pytest.raises(GFormLibError):
            raise AuthenticationError("fail")


class TestFormCreationError:
    def test_stores_config(self) -> None:
        err = FormCreationError("oops", config={"title": "T"})
        assert err.config == {"title": "T"}

    def test_config_defaults_to_empty_dict(self) -> None:
        err = FormCreationError("oops")
        assert err.config == {}


class TestFormUpdateError:
    def test_stores_form_id(self) -> None:
        err = FormUpdateError("oops", form_id="abc123")
        assert err.form_id == "abc123"

    def test_form_id_defaults_to_none(self) -> None:
        err = FormUpdateError("oops")
        assert err.form_id is None


class TestInvalidConfigError:
    def test_stores_field(self) -> None:
        err = InvalidConfigError("bad value", field="questions[0].type")
        assert err.field == "questions[0].type"

    def test_field_defaults_to_none(self) -> None:
        err = InvalidConfigError("bad value")
        assert err.field is None


class TestAPIError:
    def test_stores_status_code_and_details(self) -> None:
        err = APIError("api fail", status_code=403, details={"reason": "forbidden"})
        assert err.status_code == 403
        assert err.details == {"reason": "forbidden"}

    def test_defaults(self) -> None:
        err = APIError("api fail")
        assert err.status_code is None
        assert err.details == {}
