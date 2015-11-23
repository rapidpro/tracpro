Running Tests
=============

TracPro uses `Travis CI <https://travis-ci.org/rapidpro/tracpro>`_
to automatically build and test code upon each push to GitHub.

For the Travis build to pass, all tests should pass, code coverage should be
greater than 75%, and no Flake8 errors should exist.

To run the Django tests for all ``tracpro`` apps, run this command::

    python manage.py test

You can also run the tests with coverage and check the code coverage results::

    coverage run manage.py test
    coverage report

To see HTML output of the coverage results (which is usually easier to read),
run ``coverage html`` after running tests with coverage, then navigate to
the file ``htmlcov/index.html`` (relative to the project root) in your browser.

To check `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ and
`pyflakes <https://github.com/pyflakes/pyflakes/>`_ compliance::

    flake8

Errors & their locations will be output; no output indicates success.