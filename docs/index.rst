gformlib
========

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   authentication

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog
   contributing

Overview
--------

**gformlib** is a Python library for creating and managing Google Forms
programmatically from a Python dict or JSON file.

It is a high-level wrapper around the official
`Google Forms API v1 <https://developers.google.com/forms/api/reference/rest>`_.

Features
~~~~~~~~

* Create Google Forms from a simple Python dict or JSON.
* All nine question types: short answer, paragraph, multiple choice,
  checkboxes, dropdown, linear scale, date, time, and file upload.
* Service-account and OAuth 2.0 authentication.
* Full type annotations (PEP 561 compliant).
* Retrieve form responses with automatic pagination.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
