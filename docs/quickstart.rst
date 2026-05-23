Quickstart
==========

This guide shows the most common usage patterns.

Create a form
-------------

.. code-block:: python

    from gformlib import GoogleFormsClient

    client = GoogleFormsClient.from_service_account("service_account.json")

    info = client.create_form(
        {
            "title": "Customer Satisfaction Survey",
            "description": "Help us improve our service.",
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
                    "options": ["Dashboard", "Reports", "API"],
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

Load config from a JSON file
-----------------------------

.. code-block:: python

    import json
    from gformlib import GoogleFormsClient

    with open("my_form.json") as f:
        config = json.load(f)

    client = GoogleFormsClient.from_service_account("service_account.json")
    info = client.create_form(config)

Read responses
--------------

.. code-block:: python

    responses = client.list_responses(info.form_id)
    for r in responses:
        print(r["responseId"])

Retrieve form metadata
-----------------------

.. code-block:: python

    form_data = client.get_form(info.form_id)
    print(form_data["info"]["title"])

Question types reference
------------------------

.. list-table::
   :header-rows: 1

   * - ``type`` value
     - Google Forms equivalent
   * - ``short_answer``
     - Short answer (single line)
   * - ``paragraph``
     - Paragraph (multi-line)
   * - ``multiple_choice``
     - Multiple choice (radio)
   * - ``checkboxes``
     - Checkboxes
   * - ``dropdown``
     - Dropdown
   * - ``scale``
     - Linear scale
   * - ``date``
     - Date
   * - ``time``
     - Time
   * - ``file_upload``
     - File upload
