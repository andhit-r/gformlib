Installation
============

Requirements
------------

* Python 3.9 or newer
* A Google Cloud project with the **Google Forms API** and
  **Google Drive API** enabled.

Installing from PyPI
--------------------

.. code-block:: bash

    pip install gformlib

Installing from source
----------------------

.. code-block:: bash

    git clone https://github.com/andhit-r/gformlib.git
    cd gformlib
    pip install -e ".[dev]"

Development dependencies (testing, linting, type-checking) are installed
via the ``[dev]`` extra.  Documentation dependencies are available via the
``[docs]`` extra:

.. code-block:: bash

    pip install -e ".[dev,docs]"
