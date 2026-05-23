# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] – 2024-05-23

### Added
- Initial release.
- `GoogleFormsClient` with `from_service_account`, `from_service_account_info`,
  and `from_oauth_credentials` factory methods.
- `create_form` – create a Google Form from a Python dict / JSON.
- `get_form` – retrieve form metadata.
- `list_responses` – list all responses with automatic pagination.
- `delete_form` – move a form to the Drive trash.
- `FormBuilder` for converting `FormConfig` into Google Forms API payloads.
- All nine question types: short answer, paragraph, multiple choice, checkboxes,
  dropdown, scale, date, time, file upload.
- Full docstrings, type annotations, and PEP 561 `py.typed` marker.
- Unit tests with pytest and `pytest-mock`.
- GitHub Actions: test, publish to PyPI, build GHCR image, ReadTheDocs docs trigger.
- Sphinx documentation with ReadTheDocs theme.

[Unreleased]: https://github.com/andhit-r/gformlib/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/andhit-r/gformlib/releases/tag/v0.1.0
