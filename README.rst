I8t - Introspect client library
===============================

.. image:: https://img.shields.io/pypi/v/i8t.svg
   :target: https://pypi.org/project/i8t

.. image:: https://img.shields.io/pypi/pyversions/i8t.svg

.. image:: https://github.com/peterdemin/i8t/workflows/tests/badge.svg
   :target: https://github.com/peterdemin/i8t/actions?query=workflow%3A%22tests%22
   :alt: tests

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: Black

``i8t`` instruments Python code to send checkpoints to i8t server.

Installation
------------

.. code-block:: bash

    pip install i8t

Usage
-----

i8t can be used in a few ways:

1. Instrument all inbound web requests (currently only Flask is supported):

   .. code-block:: python

        import flask
        import requests
        from i8t.instrument.flask_introspect import FlaskIntrospect

        app = flask.Flask(__name__)

        app.route("/test", methods=["POST"])
        def test_route():
            return "Test Response", 200
      
        introspect_client = IntrospectClient(
            session=requests.Session(),
            api_url="https://api.demin.dev/i8t/checkpoints/unique-tenant-id",
            name="app",
        )
        flask_introspect = FlaskIntrospect(introspect_client)
        flask_introspect.register(app)

2. Instrument all outbound HTTP requests (currently only requests is supported):

   .. code-block:: python

        import requests
        from i8t.instrument.requests_introspect import RequestsIntrospect

        introspect_client = IntrospectClient(
            session=requests.Session(),
            api_url="https://api.demin.dev/i8t/checkpoints/unique-tenant-id",
            name="app",
        )
        requests_introspect = RequestsIntrospect(introspect_client)
        requests_introspect.register()

3. Decorate any function to send its inputs and outputs:

   .. code-block:: python

        from i8t.client import IntrospectClient, IntrospectDecorator, introspect

        @introspect
        def test_func(first, second):
            return first + second

        introspect_client = IntrospectClient(
            session=requests.Session(),
            api_url="https://api.demin.dev/i8t/checkpoints/unique-tenant-id",
            name="app",
        )
        decorator = IntrospectDecorator(introspect_client)
        decorator.register()

Once initialized, the inputs and outputs of the instrumented calls are sent to the i8t server,
where they can be later fetched at the same URL.

The fetched call checkpoints can be used to set up canned tests.
