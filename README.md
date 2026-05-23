# gformlib

[![PyPI version](https://badge.fury.io/py/gformlib.svg)](https://pypi.org/project/gformlib/)
[![Python versions](https://img.shields.io/pypi/pyversions/gformlib.svg)](https://pypi.org/project/gformlib/)
[![CI](https://github.com/andhit-r/gformlib/actions/workflows/test.yml/badge.svg)](https://github.com/andhit-r/gformlib/actions/workflows/test.yml)
[![Documentation Status](https://readthedocs.org/projects/gformlib/badge/?version=latest)](https://gformlib.readthedocs.io/en/latest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/andhit-r/gformlib/branch/main/graph/badge.svg)](https://codecov.io/gh/andhit-r/gformlib)

**gformlib** is a Python library for creating and managing Google Forms programmatically from JSON configurations. It is a high-level wrapper around the official [Google Forms API v1](https://developers.google.com/forms/api/reference/rest).

## Features

- Create Google Forms from a simple Python dict / JSON file
- All question types supported: short answer, paragraph, multiple choice, checkboxes, dropdown, scale, date, time, file upload
- Service-account and OAuth 2.0 authentication
- Full type annotations (PEP 561 compliant)
- Retrieve form responses with automatic pagination
- Professional project structure, ready to publish to PyPI

## Installation

```bash
pip install gformlib
```

## Quickstart

### 1. Authenticate with a Service Account (recommended for servers)

```python
from gformlib import GoogleFormsClient

client = GoogleFormsClient.from_service_account("path/to/service_account.json")
```

### 2. Authenticate with OAuth 2.0 (desktop / installed apps)

```python
client = GoogleFormsClient.from_oauth_credentials(
    "client_secrets.json",
    token_file="token.json",
)
```

### 3. Create a form from a dict

```python
info = client.create_form(
    {
        "title": "Customer Satisfaction Survey",
        "description": "Tell us how we're doing.",
        "questions": [
            {
                "title": "Your name",
                "type": "short_answer",
                "required": True,
            },
            {
                "title": "Overall rating",
                "type": "scale",
                "low": 1,
                "high": 5,
                "low_label": "Poor",
                "high_label": "Excellent",
                "required": True,
            },
            {
                "title": "Which features do you use?",
                "type": "checkboxes",
                "options": ["Dashboard", "Reports", "API", "Integrations"],
            },
            {
                "title": "Any other comments?",
                "type": "paragraph",
            },
        ],
    }
)

print(f"Form ID   : {info.form_id}")
print(f"Share URL : {info.responder_uri}")
```

### 4. Read responses

```python
responses = client.list_responses(info.form_id)
for r in responses:
    print(r["responseId"], r.get("answers"))
```

## Supported question types

| `type` value      | Google Forms equivalent      |
|-------------------|------------------------------|
| `short_answer`    | Short answer (single line)   |
| `paragraph`       | Paragraph (multi-line)       |
| `multiple_choice` | Multiple choice (radio)      |
| `checkboxes`      | Checkboxes                   |
| `dropdown`        | Dropdown                     |
| `scale`           | Linear scale                 |
| `date`            | Date                         |
| `time`            | Time                         |
| `file_upload`     | File upload                  |

## Authentication setup

### Service Account

1. Create a Service Account in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Forms API** and **Google Drive API**.
3. Download the JSON key file.
4. Share the target Google Drive folder with the service account email.

### OAuth 2.0

1. Create an OAuth 2.0 **Desktop app** client in Google Cloud Console.
2. Download `client_secrets.json`.
3. On first run, a browser window opens to authorise access.
4. The token is cached in `token.json` for subsequent runs.

## Development

```bash
git clone https://github.com/andhit-r/gformlib.git
cd gformlib
pip install -e ".[dev]"
pytest
```

### Running the full test matrix with tox

```bash
tox
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
